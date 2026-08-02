<table>
<tr>
<td width="170" align="center">

<img src="assets/logo.png" alt="Sphero Revived Logo" width="150">

</td>

<td>

# Sphero Revived

### Reviving the Fun, One Sphero at a Time.

Sphero Revived is an open-source preservation project dedicated to **fixing, studying, and eventually restoring** the lost functionality and fun that made legacy Sphero robots so special.

The project began with a BB-8 that had been unusable for more than three years and only advertised itself as `OTA UPDATE`. By reverse engineering its Qualcomm/CSR OTA protocol and EEPROM application-image format, it became possible to restore the droid entirely over Bluetooth without desoldering or externally programming its EEPROM.

What started as an attempt to save a single BB-8 has now become a long-term effort to preserve and revive as many legacy Sphero products as possible.

</td>
</tr>
</table>

---

## Current Release

This beta currently contains a command-line recovery tool for **Sphero BB-8**.

### Stable Recovery

**Recommended for all users.**

This recovery path has been **verified on real BB-8 hardware**.

It restores the known working donor application (`BB-278B`). Once the recovery is complete, simply connect the droid using **Sphero Edu** and allow the official firmware update if prompted.

This method always restores the donor identity:

- **Name:** `BB-278B`
- **MAC Address:** Donor MAC

This doesn't cause any known issues during normal use, but it's something to keep in mind.

---

### Experimental Randomized Identity Recovery

This mode is still **experimental**.

Instead of restoring the verified donor image directly, Sphero Revived creates a modified copy containing newly generated identity-related data while keeping the image structurally valid.

The goal of this mode is to avoid every recovered BB-8 sharing the exact same identity.

At the moment we still don't completely understand how the firmware generates the final Bluetooth identity, so this feature requires additional testing on real hardware before it can become the recommended recovery method.

Eventually, with enough community testing and recovery reports, I'd like to fully reverse engineer this process so users can preserve—or even restore—their original BB-8 identity.

---

### Other Features

- Read-only diagnostic scan
- JSON recovery reports
- Bluetooth-only recovery
- No EEPROM programmer required

## Current release

This beta contains a command-line BB-8 recovery tool for Linux:

- **Stable Recovery** — hardware-verified; restores the known working donor
  application as `BB-278B`, after which Sphero Edu can complete its update.
  
  This is the recomended recovery method for now.
  It will quickly return your BB-8 to life using a dump from a donor unit,
  That would fix the droid but restoring it with this method will always result in a droid with the name "BB-278B" and same MAC address, For normal use this doesn't cause any known issues, but it's something to keep in mind. 🙂
  
- **Experimental randomized identity recovery** — builds a CRC-valid copy with
  new identity-related data. This path is **not yet tested on physical hardware**.
- Read-only scanning and structured JSON recovery reports.

This one is marked as experimental mainly because we still need more testing on real units to fully reverse engineer the process of assigning a specific MAC address.
This method uses everything we've learned so far to generate a new "custom" identity each time you restore with this method.
Eventually with more testing and logs from people using this tool we can implement a way to preserve the original MAC and droid name and move this method to the main implementation


## Installation

### Linux (SteamOS and other distributions)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python run.py
```

Or launch a specific mode directly:

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
reported name, and allow the official firmware update if prompted.

## What's Next?

Recovery was the main goal when I started this project... but now it's only the beginning.

The long-term vision for Sphero Revived is to support as many legacy Sphero robots as possible while restoring the games, personalities, animations, and other features that disappeared alongside their original mobile apps.

Hopefully, one day these little droids will be just as fun as they were when they first came out.

Support for **SPRK** and **Ollie** is already planned since I currently own both robots.

Support for additional products—including **BB-9E**, **R2-D2**, **R2-Q5**, **Lightning McQueen**, **Spider-Man**, and others—will require access to real hardware before official support can be developed and tested.

See the [Compatibility Table](docs/COMPATIBILITY.md) and the [Project Roadmap](docs/ROADMAP.md).

## Credits

Special thanks to u/Stroker347 who preserved and shared the
working and OTA-stuck BB-8 EEPROM dumps that made this research possible
Without all his help, this project would not exist like it does now.

Sphero, BB-8, and other product names are trademarks of their respective owners.
This is an independent community preservation project and is not affiliated
with or endorsed by Sphero or Disney/Lucasfilm.



## ❤️ Support the Project

Sphero Revived is a completely free and open-source preservation project.

The goal isn't just to recover BB-8s
it's to eventually restore as many legacy Sphero robots and their original features as possible.

One of the biggest challenges is simply access to hardware. Some robots are difficult (and expensive) to obtain where I'm located, and testing on real hardware is essential before official support can be added.

If you'd like to help the project grow, there are several ways you can contribute:

- ⭐ Star the repository
- 🐛 Report bugs and submit recovery reports
- 💻 Contribute code or documentation
- 🤖 Donate compatible Sphero robots for research and testing

Hardware donations are never expected
I'll continue growing the project whether donations happen or not. 
Donated hardware simply allows me to support more robots sooner.



