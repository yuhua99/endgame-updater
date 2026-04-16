# Endgame Firmware Updater

This repository contains a small Python script that downloads Endgame trackball firmware from GitHub, verifies its SHA-256 hash, and copies it to the device when it appears as a UF2 drive.

## Requirements

- Python 3
- Internet access
- The trackball connected over USB

## Usage

Install the latest release:

```bash
python3 update_endgame.py
```

Install a specific release version:

```bash
python3 update_endgame.py 0.5.12
```

The script will ask:

```text
Use 3395 version? [y/N]
```

Press `y` for the PAW3395 firmware, or press Enter for the normal firmware.

## How it works

1. Checks the latest release, or the requested version, from `efogtech/endgame-trackball-config`
2. Prompts for normal or PAW3395 firmware
3. Downloads the matching `.uf2` firmware file
4. Verifies the downloaded firmware against the SHA-256 digest published in the GitHub release asset metadata
5. Waits for the trackball to appear in bootloader mode
6. Copies the firmware onto the UF2 drive

## Updating the device

1. Start the script
2. Put the trackball into reset or bootloader mode when prompted
3. Wait for the file copy to finish
4. The script verifies the firmware hash before copying
5. The device should reboot automatically

## Notes

- Version arguments should be plain versions like `0.5.12`
- The script adds the GitHub release tag prefix internally
- The default answer to `Use 3395 version? [y/N]` is `No`
- The script requires the selected GitHub release asset to include a `sha256:` digest
- The script looks for common UF2 mount points on Windows, Linux, and macOS
