# Sphero Revived

**Reviving the Fun, One Sphero at a Time.**

Sphero Revived is an open-source preservation project for repairing, studying,
and eventually restoring the discontinued experiences that made legacy Sphero
robots special.

The project began with a BB-8 that had been unusable for more than three years
and only advertised as `OTA UPDATE`. Its Qualcomm/CSR OTA protocol and EEPROM
application-image format were reconstructed, allowing the droid to be restored
entirely over Bluetooth without desoldering or externally programming the
EEPROM.

## Current release

This beta contains a command-line BB-8 recovery tool for Linux:

- **Stable Recovery** — hardware-verified; restores the known working donor
  application as `BB-278B`, after which Sphero Edu can complete its update.
- **Experimental randomized identity recovery** — builds a CRC-valid copy with
  new identity-related data. This path is **not yet tested on physical hardware**.
- Read-only scanning and structured JSON recovery reports.

## Install on SteamOS / Linux

```bash
cd SpheroRevived-v1.0.0-beta
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Run a specific mode directly:

```bash
python run.py diagnose
python run.py stable
python run.py experimental
```

Use `--ota-address XX:XX:XX:XX:XX:XX` when more than one `OTA UPDATE` device is
nearby or discovery by name is unreliable.

## Safety

Firmware recovery always carries risk. Keep BB-8 stationary on a powered
charger and prevent the computer from sleeping. Do not interrupt a transfer
after `START`.

The stable path has been successfully tested on original BB-8 hardware. The
experimental identity path has only been proven structurally and by offline CRC
validation. It may leave a droid unable to boot, and the continued availability
of `OTA UPDATE` after such a failure is not yet hardware-proven.

## After recovery

When a `BB-xxxx` device is detected, open Sphero Edu, select BB-8, connect to the
reported name, and permit the official firmware update if prompted.

## Project direction

Recovery is only the beginning. The long-term goal is to support as many legacy
Sphero products as possible and restore games, behaviors, personality, and
other functionality abandoned with their original applications.

See [compatibility](docs/COMPATIBILITY.md) and the [roadmap](docs/ROADMAP.md).

## Credits

Special thanks to the Reddit community contributor who preserved and shared the
working and OTA-stuck BB-8 EEPROM dumps that made this research possible. Add
his preferred public username here before publishing the repository.

Sphero, BB-8, and other product names are trademarks of their respective owners.
This is an independent community preservation project and is not affiliated
with or endorsed by Sphero or Disney/Lucasfilm.
