#!/usr/bin/env python3
"""Prepare AdminDesk Windows branding assets from the approved logo PNG."""
import argparse
import base64
import io
import json
from pathlib import Path
from PIL import Image

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logo", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path(".github/config/AdminDesk.json"))
    parser.add_argument("--icon", type=Path, default=Path(".github/assets/AdminDesk.ico"))
    args = parser.parse_args()
    if not args.logo.is_file():
        parser.error(f"Approved AdminDesk logo not found: {args.logo}")
    with Image.open(args.logo) as source:
        image = source.convert("RGBA")
        if image.width != image.height:
            parser.error("AdminDesk icon must be square")
        args.icon.parent.mkdir(parents=True, exist_ok=True)
        image.save(args.icon, format="ICO", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
    config = json.loads(args.config.read_text(encoding="utf-8"))
    config["appname"] = "AdminDesk"
    config["iconbase64"] = base64.b64encode(args.icon.read_bytes()).decode("ascii")
    config["logobase64"] = base64.b64encode(args.logo.read_bytes()).decode("ascii")
    args.config.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Prepared AdminDesk ICO and embedded logo/icon in configuration")

if __name__ == "__main__":
    main()
