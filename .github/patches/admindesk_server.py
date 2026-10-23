#!/usr/bin/env python3
"""Validate and apply RDGen's AdminDesk server settings to RustDesk 1.5.0."""
import argparse
import json
import re
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--rustdesk-root", required=True)
    args = p.parse_args()
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if cfg.get("platform") != "windows" or cfg.get("version") != "1.5.0":
        raise SystemExit("Expected Windows RustDesk 1.5.0 config")
    host, key = cfg.get("serverIP", "").strip(), cfg.get("key", "").strip()
    if not host or not key:
        raise SystemExit("serverIP and public key are required")
    port = int(cfg.get("serverPort") or 21116)
    if not 1 <= port <= 65532:
        raise SystemExit("Invalid rendezvous port")
    root = Path(args.rustdesk_root)
    config = root / "libs/hbb_common/src/config.rs"
    source = config.read_text(encoding="utf-8")
    def replace_one(pattern, value, label):
        nonlocal source
        source, count = re.subn(pattern, lambda match: match.expand(value) if label in ("RENDEZVOUS_PORT", "RELAY_PORT", "WS_RENDEZVOUS_PORT", "WS_RELAY_PORT") else value, source, count=1)
        if count != 1:
            raise SystemExit(f"Could not patch {label} in config.rs")
    replace_one(r"rs-ny\.rustdesk\.com", host, "server")
    replace_one(r"OeVuKk5nlHiXp\+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=", key, "public key")
    for name, value in (("RENDEZVOUS_PORT", port), ("RELAY_PORT", port+1),
                        ("WS_RENDEZVOUS_PORT", port+2), ("WS_RELAY_PORT", port+3)):
        replace_one(rf"(pub const {name}: i32 = )\d+;", rf"\g<1>{value};", name)
    config.write_text(source, encoding="utf-8")
    print("AdminDesk server and public key embedded in RustDesk config.rs")

if __name__ == "__main__":
    main()
