#!/usr/bin/env python3
"""Generate a native Shadowrocket config from META.yaml plus the bundled module.

META.yaml is the single source of truth for routing/policy/DNS/hosts. The
existing All-in-One.sgmodule is treated as an intermediate build artifact and
is flattened into the final config, with module arguments resolved to their
current default values.
"""
from __future__ import annotations

import ipaddress
import re
import urllib.request
from collections import OrderedDict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "META.yaml"
MODULE = ROOT / "Shadowrocket/Modules/All-in-One.sgmodule"
RULE_DIR = ROOT / "Shadowrocket/Rules"
OUTPUT = ROOT / "Shadowrocket/Shadowrocket.conf"

RAW_BASE = "https://raw.githubusercontent.com/styxiik/myrules/main"
UPDATE_URL = f"{RAW_BASE}/Shadowrocket/Shadowrocket.conf"
SECTION_RE = re.compile(r"^\[([^\]]+)\]\s*$")
PLACEHOLDER_RE = re.compile(r"\{\{\{([^}]+)\}\}\}")
RULE_PREFIXES = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-WILDCARD",
    "USER-AGENT", "URL-REGEX", "IP-CIDR", "IP-CIDR6", "IP-ASN",
    "GEOIP", "DST-PORT", "SRC-PORT", "PROTOCOL", "AND", "OR", "NOT",
}


def fetch_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "styxiik-myrules-shadowrocket-config/1.0"},
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read().decode("utf-8-sig")


def parse_module(text: str) -> tuple[dict[str, str], OrderedDict[str, list[str]]]:
    defaults: dict[str, str] = {}
    sections: OrderedDict[str, list[str]] = OrderedDict()
    current: str | None = None

    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.rstrip()
        if line.startswith("#!arguments="):
            value = line.split("=", 1)[1].strip()
            for item in value.split(","):
                if ":" in item:
                    key, default = item.split(":", 1)
                    defaults[key.strip()] = default.strip()
            continue
        m = SECTION_RE.match(line.strip())
        if m:
            current = m.group(1).strip()
            sections.setdefault(current, [])
            continue
        if current is not None and line.strip():
            sections[current].append(line)

    return defaults, sections


def resolve_module_arguments(line: str, defaults: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in defaults:
            raise RuntimeError(f"Module placeholder has no default value: {key}")
        return defaults[key]
    line = PLACEHOLDER_RE.sub(repl, line)
    # %APPEND% / %INSERT% are module merge directives. Once the module is
    # flattened into the standalone main config there is nothing to merge
    # with, so emit the underlying value as ordinary config syntax.
    line = re.sub(r"(=\s*)%(?:APPEND|INSERT)%\s*", r"\1", line)
    return line


def provider_items(provider: dict[str, Any]) -> list[str]:
    if provider.get("type") == "inline":
        raw = provider.get("payload", [])
        return [str(x).strip() for x in raw if str(x).strip()]

    url = provider.get("url")
    if not url:
        raise RuntimeError(f"HTTP/file provider without usable url: {provider}")

    url_s = str(url)
    own_prefixes = (
        "https://raw.githubusercontent.com/styxiik/myrules/main/",
    )
    local_text: str | None = None
    for prefix in own_prefixes:
        if url_s.startswith(prefix):
            rel = url_s[len(prefix):]
            local_path = ROOT / rel
            if local_path.exists():
                local_text = local_path.read_text(encoding="utf-8")
            break
    text = local_text if local_text is not None else fetch_text(url_s)

    try:
        obj = yaml.safe_load(text)
    except yaml.YAMLError:
        obj = None
    if isinstance(obj, dict) and isinstance(obj.get("payload"), list):
        return [str(x).strip() for x in obj["payload"] if str(x).strip()]
    if isinstance(obj, list):
        return [str(x).strip() for x in obj if str(x).strip()]

    out: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line == "payload:":
            continue
        if line.startswith("-"):
            line = line[1:].strip().strip("'\"")
        if line:
            out.append(line)
    return out


def normalize_typed_rule(item: str, force_no_resolve: bool) -> str:
    item = item.strip().strip("'\"")
    parts = [p.strip() for p in item.split(",")]
    if not parts:
        return item
    typ = parts[0].upper()
    if typ == "NETWORK" and len(parts) >= 2:
        parts[0] = "PROTOCOL"
    if parts[0].upper() == "IP-CIDR" and len(parts) >= 2 and ":" in parts[1]:
        parts[0] = "IP-CIDR6"
    if force_no_resolve and parts[0].upper() in {"IP-CIDR", "IP-CIDR6", "GEOIP", "IP-ASN"}:
        if not any(p.lower() == "no-resolve" for p in parts[2:]):
            parts.append("no-resolve")
    return ",".join(parts)


def convert_provider_item(item: str, behavior: str, force_no_resolve: bool) -> str:
    item = item.strip().strip("'\"")
    if not item:
        return ""

    head = item.split(",", 1)[0].upper()
    if head in RULE_PREFIXES or head == "NETWORK":
        return normalize_typed_rule(item, force_no_resolve)

    if behavior == "ipcidr":
        try:
            network = ipaddress.ip_network(item, strict=False)
            typ = "IP-CIDR6" if network.version == 6 else "IP-CIDR"
            suffix = ",no-resolve" if force_no_resolve else ""
            return f"{typ},{item}{suffix}"
        except ValueError:
            raise RuntimeError(f"Invalid ipcidr provider entry: {item}")

    if item.startswith("+."):
        return f"DOMAIN-SUFFIX,{item[2:]}"
    if item.startswith("."):
        return f"DOMAIN-WILDCARD,*{item}"
    if "*" in item or "?" in item:
        return f"DOMAIN-WILDCARD,{item}"
    return f"DOMAIN,{item}"


def referenced_rule_sets(meta: dict[str, Any]) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for rule in meta.get("rules", []) or []:
        if not isinstance(rule, str) or not rule.startswith("RULE-SET,"):
            continue
        parts = [p.strip() for p in rule.split(",")]
        if len(parts) < 3:
            continue
        name = parts[1]
        force_no_resolve = any(p.lower() == "no-resolve" for p in parts[3:])
        out[name] = out.get(name, False) or force_no_resolve
    return out


def build_native_rule_sets(meta: dict[str, Any]) -> dict[str, str]:
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    providers = meta.get("rule-providers", {}) or {}
    required = referenced_rule_sets(meta)
    urls: dict[str, str] = {}

    expected_files: set[Path] = set()
    for name, force_no_resolve in required.items():
        provider = providers.get(name)
        if not isinstance(provider, dict):
            raise RuntimeError(f"Referenced rule-provider not found: {name}")
        behavior = str(provider.get("behavior", "classical")).lower()
        items = provider_items(provider)
        converted: list[str] = []
        seen: set[str] = set()
        for item in items:
            line = convert_provider_item(item, behavior, force_no_resolve)
            if line and line not in seen:
                converted.append(line)
                seen.add(line)
        if not converted:
            raise RuntimeError(f"Converted provider is empty: {name}")

        path = RULE_DIR / f"{name}.list"
        path.write_text("\n".join(converted) + "\n", encoding="utf-8")
        expected_files.add(path)
        urls[name] = f"{RAW_BASE}/Shadowrocket/Rules/{name}.list"

    for stale in RULE_DIR.glob("*.list"):
        if stale not in expected_files:
            stale.unlink()
    return urls


def proxy_groups(meta: dict[str, Any]) -> list[str]:
    providers = set((meta.get("proxy-providers", {}) or {}).keys())
    out: list[str] = []
    for group in meta.get("proxy-groups", []) or []:
        if not isinstance(group, dict) or not group.get("name"):
            continue
        name = str(group["name"])
        typ = str(group.get("type", "select"))
        if typ not in {"select", "url-test", "fallback", "load-balance", "random"}:
            raise RuntimeError(f"Unsupported Shadowrocket proxy group type {typ!r} in {name}")
        fields: list[str] = [typ]
        fields.extend(str(x) for x in (group.get("proxies") or []))

        use = [str(x) for x in (group.get("use") or [])]
        if use:
            missing = [x for x in use if x not in providers]
            if missing:
                raise RuntimeError(f"Group {name} references missing proxy provider(s): {missing}")
            fields.extend(use)
            fields.append("use=true")

        if group.get("filter"):
            fields.append(f"policy-regex-filter={group['filter']}")
        if group.get("url") and typ in {"url-test", "fallback", "load-balance"}:
            fields.append(f"url={group['url']}")
        if group.get("interval") and typ in {"url-test", "fallback", "load-balance"}:
            fields.append(f"interval={group['interval']}")

        out.append(f"{name} = " + ",".join(fields))
    return out


def translate_meta_rule(rule: str, rule_urls: dict[str, str]) -> str | None:
    rule = rule.strip()
    if not rule:
        return None
    if rule.startswith("SUB-RULE,"):
        return None
    if rule.startswith("RULE-SET,"):
        chunks = [p.strip() for p in rule.split(",")]
        if len(chunks) < 3:
            raise RuntimeError(f"Invalid RULE-SET line: {rule}")
        name, policy = chunks[1], chunks[2]
        if name not in rule_urls:
            raise RuntimeError(f"No generated Shadowrocket ruleset for {name}")
        return f"RULE-SET,{rule_urls[name]},{policy}"
    if rule.startswith("MATCH,"):
        return "FINAL," + rule.split(",", 1)[1]
    return re.sub(r"\(NETWORK,([^)]+)\)", r"(PROTOCOL,\1)", rule)


def general_lines(meta: dict[str, Any], module_general: list[str]) -> list[str]:
    dns = meta.get("dns", {}) or {}
    nameservers = [str(x) for x in (dns.get("nameserver") or dns.get("default-nameserver") or ["system"])]
    proxy_ns = [str(x) for x in (dns.get("proxy-server-nameserver") or [])]
    fake_filters = [str(x) for x in (dns.get("fake-ip-filter") or [])]

    base = [
        "yaml = true",
        "udp-policy-not-supported-behaviour = REJECT",
        "skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, captive.apple.com",
        "tun-excluded-routes = 239.255.255.250/32, 224.0.0.251/32, ff02::fb/128",
        "dns-server = " + ", ".join(nameservers),
    ]
    if proxy_ns:
        base.append("proxy-dns-server = " + ", ".join(proxy_ns))
    if fake_filters:
        base.append("always-real-ip = " + ",".join(fake_filters))
    base.extend([
        f"ipv6 = {'true' if meta.get('ipv6', True) else 'false'}",
        f"update-url = {UPDATE_URL}",
    ])

    merged: OrderedDict[str, str] = OrderedDict()
    raw_lines: list[str] = []
    for line in base + module_general:
        if "=" in line and not line.lstrip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            merged[key] = line
        elif line not in raw_lines:
            raw_lines.append(line)
    return list(merged.values()) + raw_lines


def host_lines(meta: dict[str, Any]) -> list[str]:
    hosts = meta.get("hosts", {}) or {}
    return [f"{k} = {v}" for k, v in hosts.items()]


def emit_section(lines: list[str], name: str, content: list[str]) -> None:
    if not content:
        return
    lines.extend([f"[{name}]", *content, ""])


def main() -> None:
    meta = yaml.safe_load(META.read_text(encoding="utf-8"))
    if not isinstance(meta, dict):
        raise SystemExit("META.yaml did not parse as a mapping")
    if not MODULE.exists():
        raise SystemExit("All-in-One.sgmodule is missing; run build_shadowrocket_bundle.py first")

    defaults, module_sections = parse_module(MODULE.read_text(encoding="utf-8"))
    for section, rows in list(module_sections.items()):
        module_sections[section] = [resolve_module_arguments(x, defaults) for x in rows]

    rule_urls = build_native_rule_sets(meta)
    meta_rules = [
        translated
        for raw in (meta.get("rules", []) or [])
        if isinstance(raw, str)
        for translated in [translate_meta_rule(raw, rule_urls)]
        if translated
    ]

    module_rules = module_sections.get("Rule", [])
    rules: list[str] = []
    seen: set[str] = set()
    for line in module_rules + meta_rules:
        if line not in seen:
            rules.append(line)
            seen.add(line)

    lines = [
        "# AUTO-GENERATED. DO NOT EDIT.",
        "# Source of truth: /META.yaml",
        "# Shadowrocket-only module content is flattened from /Shadowrocket/Modules/All-in-One.sgmodule.",
        "# Generated rules under /Shadowrocket/Rules are build artifacts.",
        "",
    ]
    emit_section(lines, "General", general_lines(meta, module_sections.get("General", [])))
    emit_section(lines, "Proxy Group", proxy_groups(meta))
    emit_section(lines, "Rule", rules)

    hosts = host_lines(meta)
    module_hosts = module_sections.get("Host", [])
    emit_section(lines, "Host", hosts + [x for x in module_hosts if x not in hosts])

    for section in ("URL Rewrite", "Header Rewrite", "Script", "MITM"):
        emit_section(lines, section, module_sections.get(section, []))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output = "\n".join(lines).rstrip() + "\n"

    required = [
        "[Proxy Group]",
        "[Rule]",
        "FINAL,最终选择",
        "DOMAIN-SUFFIX,ts.net,TAILSCALE",
        "prefer-ipv6 = false",
        "dns-direct-system = true",
        "direct-dns-server = system",
        "[Script]",
        "[MITM]",
    ]
    for marker in required:
        if marker not in output:
            raise SystemExit(f"Generated Shadowrocket config missing required marker: {marker}")
    if PLACEHOLDER_RE.search(output):
        raise SystemExit("Generated config still contains unresolved module placeholders")

    OUTPUT.write_text(output, encoding="utf-8")
    print(f"Generated {OUTPUT.relative_to(ROOT)} ({len(output)} bytes)")
    print(f"Generated {len(rule_urls)} native Shadowrocket rule sets")


if __name__ == "__main__":
    main()
