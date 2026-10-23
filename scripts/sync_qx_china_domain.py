#!/usr/bin/env python3
"""Mirror MetaCubeX geosite cn.list and generate a native Quantumult X list.

Full geosite:cn is intentionally used; do not confuse it with the substantially
smaller geolocation-cn category. Reject unexpected/truncated upstream responses
rather than publishing broken routing rules.
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/"
    "meta/geo/geosite/cn.list"
)
CLASH_TARGET = ROOT / "Clash" / "cn.list"
QX_TARGET = ROOT / "QX" / "cn.list"
HOST_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def main() -> None:
    request = urllib.request.Request(
        SOURCE, headers={"User-Agent": "styxiik-myrules-cn-domain/2.0"}
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        source_lines = response.read().decode("utf-8-sig").splitlines()

    geosite: list[str] = []
    qx: list[str] = []
    seen: set[str] = set()
    for raw in source_lines:
        item = raw.strip()
        if not item or item.startswith("#"):
            continue
        if item.startswith("+."):
            kind, domain = "host-suffix", item[2:]
        else:
            kind, domain = "host", item
        if (
            not HOST_RE.fullmatch(domain)
            or ".." in domain
            or domain.startswith(".")
            or domain.endswith(".")
        ):
            raise ValueError(f"Unexpected MetaCubeX geosite domain: {item!r}")
        if item in seen:
            continue
        seen.add(item)
        geosite.append(item)
        qx.append(f"{kind}, {domain}")

    if len(geosite) < 100_000:
        raise RuntimeError(
            f"Refusing truncated full geosite:cn list: {len(geosite)} entries"
        )
    expected = {"+.cn", "+.xiaohongshu.com", "+.xhscdn.com", "+.qq.com"}
    missing = expected - seen
    if missing:
        raise RuntimeError(f"Required ChinaDomain entries missing: {sorted(missing)}")

    CLASH_TARGET.parent.mkdir(parents=True, exist_ok=True)
    QX_TARGET.parent.mkdir(parents=True, exist_ok=True)
    CLASH_TARGET.write_text("\n".join(geosite) + "\n", encoding="utf-8")
    QX_TARGET.write_text("\n".join(qx) + "\n", encoding="utf-8")
    print(f"Mirrored {CLASH_TARGET.relative_to(ROOT)}: {len(geosite)} domains")
    print(f"Generated {QX_TARGET.relative_to(ROOT)}: {len(qx)} QX rules")


if __name__ == "__main__":
    main()
