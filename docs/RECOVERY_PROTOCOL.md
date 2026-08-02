# Verified BB-8 Recovery Protocol

The verified target is a BB-8 stuck advertising as `OTA UPDATE` with the CSR
OTAU service `1010` and protocol version `04`.

1. Confirm `1011 == 04` and `1015 == 01` (`READY`).
2. Write `02` to `1015` (`START`).
3. Confirm `1015 == 02` (`IN_PROGRESS`).
4. Stream the exact 18,636-byte application image to `1014` in 20-byte ATT
   write requests, waiting for each request to complete.
5. Write `04` to `1015` (`COMPLETE`) only after every byte is accepted.
6. Wait for disconnect/reboot and scan for a `BB-` advertisement.
7. Connect using Sphero Edu and permit its official update if prompted.

The bundled stable image has SHA-256:

`2f2ac7352776da3b4c952e4c8103e4c5377644468ff17e8fb76bc93bcd19d895`
