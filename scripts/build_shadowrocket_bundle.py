#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import time
import urllib.request
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Shadowrocket/Modules/sources.json"
LOCAL_TAILSCALE = ROOT / "Shadowrocket/Modules/Tailscale.sgmodule"
OUTPUT = ROOT / "Shadowrocket/Modules/All-in-One.sgmodule"

SECTION_RE = re.compile(r"^\[([^\]]+)\]\s*$")
PLACEHOLDER_RE = re.compile(r"\{\{\{([^}]+)\}\}\}")
PREFERRED_SECTION_ORDER = [
    "General",
    "Rule",
    "Host",
    "URL Rewrite",
    "Header Rewrite",
    "Script",
    "MITM",
]

# Local baseline rewrites that should always be present even when upstream modules change.
BASE_URL_REWRITES = [
    r"^https?://(www\.)?g\.cn https://www.google.com 302",
    r"^https?://(www\.)?google\.cn https://www.google.com 302",
]

# HTTPS URL Rewrite needs the target hosts to pass through Shadowrocket's HTTP engine.
BASE_FORCE_HTTP_ENGINE_HOSTS = [
    "g.cn",
    "www.g.cn",
    "google.cn",
    "www.google.cn",
]

# HTTPS decryption hosts required by the local Google CN redirects.
BASE_MITM_HOSTNAMES = [
    "g.cn",
    "www.g.cn",
    "google.cn",
    "www.google.cn",
]


def fetch_text(url: str) -> str:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "styxiik-myrules-shadowrocket-bundler/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def parse_module(text: str) -> tuple[list[str], list[str], OrderedDict[str, list[str]]]:
    arguments: list[str] = []
    argument_descs: list[str] = []
    sections: OrderedDict[str, list[str]] = OrderedDict()
    current: str | None = None

    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.rstrip()
        match = SECTION_RE.match(line.strip())
        if match:
            current = match.group(1).strip()
            sections.setdefault(current, [])
            continue

        if current is None:
            if line.startswith("#!arguments="):
                value = line.split("=", 1)[1].strip()
                if value:
                    arguments.append(value)
            elif line.startswith("#!arguments-desc="):
                value = line.split("=", 1)[1].strip()
                if value:
                    argument_descs.append(value)
            continue

        if line.strip():
            sections[current].append(line)

    return arguments, argument_descs, sections


def append_unique(target: list[str], lines: list[str]) -> None:
    seen = set(target)
    for line in lines:
        if line not in seen:
            target.append(line)
            seen.add(line)


def split_append_values(value: str) -> list[str]:
    value = value.strip()
    for prefix in ("%APPEND%", "%INSERT%"):
        if value.startswith(prefix):
            value = value[len(prefix) :].strip()
            break
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = manifest.get("shadowrocket", [])
    if not entries:
        raise SystemExit("No shadowrocket sources configured in sources.json")

    merged: OrderedDict[str, list[str]] = OrderedDict()
    argument_chunks: list[str] = []
    argument_descs: list[str] = []
    hostnames: list[str] = list(BASE_MITM_HOSTNAMES)
    mitm_other: list[str] = []
    source_notes: list[str] = []

    for entry in entries:
        name = entry["name"]
        url = entry["url"]
        if name == "Tailscale":
            text = LOCAL_TAILSCALE.read_text(encoding="utf-8")
        else:
            text = fetch_text(url)

        if "[" not in text or "]" not in text:
            raise SystemExit(f"Source {name} does not look like a Shadowrocket module")

        args, arg_desc, sections = parse_module(text)
        argument_chunks.extend(args)
        argument_descs.extend(arg_desc)
        source_notes.append(f"# source: {name} -> {url}")

        for section, lines in sections.items():
            if section == "MITM":
                for line in lines:
                    if line.lstrip().startswith("hostname") and "=" in line:
                        _, value = line.split("=", 1)
                        for hostname in split_append_values(value):
                            if hostname not in hostnames:
                                hostnames.append(hostname)
                    else:
                        if line not in mitm_other:
                            mitm_other.append(line)
                continue

            merged.setdefault(section, [])
            append_unique(merged[section], lines)

    # Merge all force-http-engine-hosts declarations into one stable line, with
    # Google CN first so HTTPS redirects always enter Shadowrocket's HTTP engine.
    general_lines = merged.get("General", [])
    force_http_hosts = list(BASE_FORCE_HTTP_ENGINE_HOSTS)
    general_other: list[str] = []
    for line in general_lines:
        if line.lstrip().startswith("force-http-engine-hosts") and "=" in line:
            _, value = line.split("=", 1)
            for hostname in split_append_values(value):
                if hostname not in force_http_hosts:
                    force_http_hosts.append(hostname)
        else:
            general_other.append(line)
    merged["General"] = [
        "force-http-engine-hosts = %APPEND% " + ", ".join(force_http_hosts),
        *general_other,
    ]

    if hostnames or mitm_other:
        merged.setdefault("MITM", [])
        append_unique(merged["MITM"], mitm_other)
        if hostnames:
            merged["MITM"].append("hostname = %APPEND% " + ", ".join(hostnames))

    # Keep local Google CN redirects first so they remain stable regardless of upstream ordering.
    upstream_rewrites = merged.get("URL Rewrite", [])
    merged["URL Rewrite"] = BASE_URL_REWRITES + [
        line for line in upstream_rewrites if line not in BASE_URL_REWRITES
    ]

    # Keep Tailscale routing first so it wins before generic rules bundled from other sources.
    rules = merged.get("Rule", [])
    tailscale_rules = [line for line in rules if ",TAILSCALE" in line]
    other_rules = [line for line in rules if ",TAILSCALE" not in line]
    if tailscale_rules:
        merged["Rule"] = tailscale_rules + other_rules

    combined_arguments = ",".join(chunk for chunk in argument_chunks if chunk)
    combined_desc = r"\n\n".join(argument_descs)

    lines = [
        "#!name=MyRules All-in-One",
        "#!desc=Tailscale + Google CN redirect + BlockHTTPDNS + Zhihu + Startup Ads + Tieba + Spotify + YouTube Enhance. Auto-generated; do not edit by hand.",
        "#!author=styxiik/myrules",
    ]
    if combined_arguments:
        lines.append(f"#!arguments={combined_arguments}")
    if combined_desc:
        lines.append(f"#!arguments-desc={combined_desc}")
    lines.extend(["", "# Generated from maintained upstream modules:", *source_notes, ""])

    emitted = set()
    for section in PREFERRED_SECTION_ORDER:
        content = merged.get(section)
        if not content:
            continue
        lines.append(f"[{section}]")
        lines.extend(content)
        lines.append("")
        emitted.add(section)

    for section, content in merged.items():
        if section in emitted or not content:
            continue
        lines.append(f"[{section}]")
        lines.extend(content)
        lines.append("")

    output = "\n".join(lines).rstrip() + "\n"

    # Guard against generator regressions that would silently break editable parameters.
    placeholders = set(PLACEHOLDER_RE.findall(output))
    declared = set()
    if combined_arguments:
        for item in combined_arguments.split(","):
            declared.add(item.split(":", 1)[0].strip())
    missing = sorted(placeholders - declared)
    if missing:
        raise SystemExit(f"Undeclared module arguments referenced by scripts: {missing}")

    required = [
        "DOMAIN-SUFFIX,ts.net,TAILSCALE",
        r"^https?://(www\.)?g\.cn https://www.google.com 302",
        r"^https?://(www\.)?google\.cn https://www.google.com 302",
        "force-http-engine-hosts = %APPEND% g.cn, www.g.cn, google.cn, www.google.cn",
        "hostname = %APPEND% g.cn, www.g.cn, google.cn, www.google.cn",
        "爱奇艺_开屏去广告 =",
        "tiebac.baidu.com",
        "spotify-proto =",
        "youtube.response =",
    ]
    for marker in required:
        if marker not in output:
            raise SystemExit(f"Generated bundle is missing required marker: {marker}")

    OUTPUT.write_text(output, encoding="utf-8")
    print(f"Generated {OUTPUT.relative_to(ROOT)} ({len(output)} bytes)")


if __name__ == "__main__":
    main()
