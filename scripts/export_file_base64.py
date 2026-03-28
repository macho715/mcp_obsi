from __future__ import annotations

import argparse
import base64
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print file contents as base64.")
    parser.add_argument("--path", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = Path(args.path).read_bytes()
    print(base64.b64encode(data).decode("ascii"))


if __name__ == "__main__":
    main()
