from __future__ import annotations

import argparse
from pathlib import Path

from modelscope import snapshot_download


MODEL_ID = "Qwen/Qwen3-VL-4B-Instruct"


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the Qwen3-VL base model")
    parser.add_argument("--target", required=True, help="Target model directory")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {MODEL_ID} to {target}")
    snapshot_download(MODEL_ID, local_dir=str(target))
    if not (target / "config.json").is_file():
        raise SystemExit("Base model download appears incomplete: config.json is missing")
    print("Base model download completed.")


if __name__ == "__main__":
    main()

