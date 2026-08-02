# Experimental Randomized Identity Recovery

## What is known

Two donor EEPROM images differ in only a small set of state, integrity, and
identity-related bytes. Six device-specific bytes in the transferable
application occur at stream-relative offsets `0x78..0x7B` and `0x80..0x81`.
The verified donor contains `DD D0 D3 9A B4 0A`; the OTA-stuck donor contains
`93 37 55 98 59 17`.

## What this mode does

- Verifies the immutable donor by SHA-256 and CSR CRCs.
- Copies it into a new experiment file.
- Generates a six-byte candidate using the operating system's secure random
  source.
- Changes only those two identity-related ranges.
- Recalculates every control-block CRC and the control-header CRC.
- Independently validates the final image.
- Archives the image and a complete manifest before transfer.

## What is not known

It is not yet proven that changing these bytes produces a bootable application
or a different identity. It is also not proven that the bootloader will always
remain reachable after an unsuccessful experimental application is installed.
Therefore Stable Recovery is a likely fallback, but not a guaranteed one until
an independent hardware test confirms it.
