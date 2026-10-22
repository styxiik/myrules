#!/usr/bin/env python3
"""Generate Quantumult X ChinaDomain rules from MetaCubeX geolocation-cn.

The upstream geosite list uses "+.example.cn" suffix syntax, which Quantumult X
cannot consume directly as a normal filter list. Convert it into QX host rules.
Fail closed on empty/truncated/unexpected data so the published last-good list
is not silently replaced by an unusable file.
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/"
    "meta/geo/geosite/geolocation-cn.list"
)
TARGET = ROOT / "QX" / "geolocation-cn.list"
HOST_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def main() -> None:
    request = urllib.request.Request(
        SOURCE, headers={"User-Agent": "styxiik-myrules-qx-cn/1.0"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        source_lines = response.read().decode("utf-8-sig").splitlines()

    output: list[str] = []
    seen: set[str] = set()
    for raw in source_lines:
        item = raw.strip()
        if not item or item.startswith("#"):
            continue
        if item.startswith("+."):
            kind, domain = "host-suffix", item[2:]
        else:
            kind, domain = "host", item
        if not HOST_RE.fullmatch(domain) or ".." in domain:
            raise ValueError(f"Unexpected MetaCubeX geosite domain: {item!r}")
        line = f"{kind}, {domain}"
        if line not in seen:
            output.append(line)
            seen.add(line)

    # This source currently has ~5.4k domains. Prevent publishing broken data.
    if len(output) < 3000:
        raise RuntimeError(
            f"Refusing to publish suspicious ChinaDomain list: {len(output)} rules"
        )

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(f"Generated {TARGET.relative_to(ROOT)}: {len(output)} QX rules")


if __name__ == "__main__":
    main()
