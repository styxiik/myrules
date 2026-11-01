#!/usr/bin/env python3
"""Read-only routing regression checks. Run after the Shadowrocket generator."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
meta = yaml.safe_load((ROOT / "META.yaml").read_text(encoding="utf-8"))
qx = (ROOT / "QX.conf").read_text(encoding="utf-8")
sr = (ROOT / "Shadowrocket/Shadowrocket.conf").read_text(encoding="utf-8")

def require(ok: bool, msg: str) -> None:
    if not ok:
        raise SystemExit("Routing invariant failed: " + msg)

def section(content: str, title: str) -> str:
    marker = f"[{title}]\n"
    require(marker in content, f"missing section {title}")
    return content.split(marker, 1)[1].split("\n[", 1)[0]

excluded = {str(x) for x in meta["tun"]["route-exclude-address"]}
lan = ("192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12")
for subnet in (*lan, "fc00::/7", "100.64.0.0/10", "fd7a:115c:a1e0::/48"):
    require(subnet in excluded, "missing Mihomo exclusion " + subnet)
for subnet in ("2606:4700:a0::/123", "2606:4700:a8::/123"):
    require(subnet not in excluded, "Cloudflare Tunnel bypass reintroduced " + subnet)
require(meta["rule-providers"]["direct"]["url"].endswith("/MetaCubeX/meta-rules-dat/meta/geo/geosite/cn.list"), "Mihomo CN source")
remote, local = section(qx, "filter_remote"), section(qx, "filter_local")
require("geoip, cn, direct" not in local.lower(), "local QX GeoIP preempts remote IP rules")
require("host-wildcard, *.cn, direct" not in local.lower(), "local QX CN preempts explicit proxy")
for name in ("QX/cn.list", "QX/geolocation-!cn.list", "FILTER_REGION"):
    require(name in remote, "missing QX resource " + name)
require(remote.index("QX/cn.list") < remote.index("QX/geolocation-!cn.list"), "QX CN source order")
for name in ("QX/cfip.txt", "QX/googleip.txt", "telegramcidr.txt"):
    require(remote.index(name) < remote.index("FILTER_REGION"), "QX IP proxy before CN GeoIP: " + name)
general, rules = section(sr, "General"), section(sr, "Rule")
route = next((x for x in general.splitlines() if x.startswith("tun-excluded-routes =")), "")
require(all(x in route for x in lan), "Shadowrocket LAN routes missing")
for subnet in ("100.64.0.0/10", "fd7a:115c:a1e0::/48", "fc00::/7", "2606:4700:a0::/123", "2606:4700:a8::/123"):
    require(subnet not in route, "Shadowrocket native Tailscale/CF Tunnel bypass: " + subnet)
require("IP-CIDR6,fd7a:115c:a1e0::/48,TAILSCALE" in rules, "Shadowrocket native Tailscale IPv6 policy")
require("IP-CIDR6,2402:4e00:1200:ed00:0:9089:6dac:96b6/128,REJECT-DROP" in rules, "IPv6 module rule type")
print("Routing invariants OK: CN priority, LAN, CF Tunnel, Tailscale")
