#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
QX = ROOT / "QX.conf"
DIRECT = ROOT / "Clash" / "ClashDirect.yaml"

BEGIN = "; BEGIN DIRECT-SYSTEM-DNS"
END = "; END DIRECT-SYSTEM-DNS"
MARKER = ";指定域名解析dns"

def build_block() -> str:
    lines = [
        BEGIN,
        "; QX has no final-policy-aware DNS selector.",
        "; Default stays DoH; explicit DIRECT domains use current network system DNS.",
        "server = /*.cn/system",
        "server = /*.local/system",
    ]
    for raw in DIRECT.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*-\s+(DOMAIN|DOMAIN-SUFFIX),([^,\s]+)\s*$", raw)
        if not m:
            continue
        kind, domain = m.groups()
        if kind == "DOMAIN":
            lines.append(f"server = /{domain}/system")
        else:
            lines.append(f"server = /{domain}/system")
            lines.append(f"server = /*.{domain}/system")
    # Preserve order while removing duplicates.
    out = []
    seen = set()
    for line in lines:
        if line not in seen:
            out.append(line)
            seen.add(line)
    out.append(END)
    return "\n".join(out)

def main() -> None:
    text = QX.read_text(encoding="utf-8")
    text = re.sub(
        rf"\n{re.escape(BEGIN)}[\s\S]*?{re.escape(END)}\n",
        "\n",
        text,
    )
    if MARKER not in text:
        raise SystemExit(f"marker not found: {MARKER}")
    text = text.replace(MARKER, MARKER + "\n" + build_block(), 1)
    QX.write_text(text, encoding="utf-8")

if __name__ == "__main__":
    main()
