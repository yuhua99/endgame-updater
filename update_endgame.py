#!/usr/bin/env python3
import json
import shutil
import string
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen


REPO_OWNER = "efogtech"
REPO_NAME = "endgame-trackball-config"
POLL_SECONDS = 1
TIMEOUT_SECONDS = 120
HTTP_TIMEOUT_SECONDS = 30


def get_json(url: str) -> dict:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "endgame-trackball-updater",
        },
    )
    with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        return json.load(response)


def get_release(version: Optional[str]) -> dict:
    if version:
        api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/tags/endgame-{version}"
    else:
        api_url = (
            f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        )
    return get_json(api_url)


def pick_asset(release: dict, is_3395: bool) -> dict:
    prefix = "endgame-paw3395-" if is_3395 else "endgame-"

    for asset in release.get("assets", []):
        name = asset.get("name", "")
        if not name.endswith(".uf2"):
            continue
        if not name.startswith(prefix):
            continue
        if not is_3395 and "paw3395" in name:
            continue
        return asset

    variant = "3395" if is_3395 else "normal"
    raise RuntimeError(f"Could not find {variant} firmware in the selected release")


def download_file(url: str, destination: Path) -> None:
    request = Request(url, headers={"User-Agent": "endgame-trackball-updater"})
    with (
        urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response,
        destination.open("wb") as output,
    ):
        shutil.copyfileobj(response, output)


def is_uf2_drive(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    if (path / "INFO_UF2.TXT").exists():
        return True
    name = path.name.upper()
    return name in {"RPI-RP2", "UF2BOOT"}


def candidate_mount_points() -> list[Path]:
    candidates: list[Path] = []

    if sys.platform.startswith("win"):
        for drive in string.ascii_uppercase:
            candidates.append(Path(f"{drive}:/"))
    else:
        candidates.extend(Path("/media").glob("*/*"))
        candidates.extend(Path("/media").glob("*"))
        candidates.extend(Path("/run/media").glob("*/*"))
        candidates.extend(Path("/run/media").glob("*"))
        candidates.extend(Path("/Volumes").glob("*"))
        candidates.append(Path("/mnt"))
        candidates.extend(Path("/mnt").glob("*"))

    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def wait_for_uf2_drive() -> Path:
    print("Put the trackball into reset/bootloader mode now.")
    print("Waiting for the UF2 drive to appear...")

    deadline = time.time() + TIMEOUT_SECONDS
    while time.time() < deadline:
        for path in candidate_mount_points():
            if is_uf2_drive(path):
                return path
        time.sleep(POLL_SECONDS)

    raise RuntimeError("Timed out waiting for the UF2 drive")


def choose_variant() -> bool:
    while True:
        answer = input("Use 3395 version? [y/N] ").strip().lower()
        if answer in {"", "n", "no"}:
            return False
        if answer in {"y", "yes"}:
            return True
        print("Please enter y or n.")


def main() -> int:
    if len(sys.argv) > 2:
        name = Path(sys.argv[0]).name
        print(f"Usage: {name} [version]", file=sys.stderr)
        print(f"Example: {name} 0.5.12", file=sys.stderr)
        return 1

    version = sys.argv[1] if len(sys.argv) == 2 else None
    is_3395 = choose_variant()

    if version:
        print(f"Checking firmware release {version}...")
    else:
        print("Checking latest firmware release...")
    release = get_release(version)
    asset = pick_asset(release, is_3395)
    asset_name = asset["name"]
    asset_url = asset["browser_download_url"]
    tag = release.get("tag_name", "unknown")

    print(f"Release: {tag}")
    print(f"Selected firmware: {asset_name}")

    with tempfile.TemporaryDirectory(prefix="endgame-fw-") as temp_dir:
        firmware_path = Path(temp_dir) / asset_name
        print("Downloading firmware...")
        download_file(asset_url, firmware_path)

        drive = wait_for_uf2_drive()
        target_path = drive / asset_name
        print(f"Copying firmware to {drive}...")
        shutil.copyfile(firmware_path, target_path)

    print("Done. The device should reboot after the copy finishes.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Cancelled.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
