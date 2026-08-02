from typing import Final

OTA_NAME: Final = "OTA UPDATE"
OTA_SERVICE: Final = "00001010-d102-11e1-9b23-00025b00a5a5"
OTA_VERSION: Final = "00001011-d102-11e1-9b23-00025b00a5a5"
DATA_TRANSFER: Final = "00001014-d102-11e1-9b23-00025b00a5a5"
TRANSFER_CONTROL: Final = "00001015-d102-11e1-9b23-00025b00a5a5"

START: Final = b"\x02"
COMPLETE: Final = b"\x04"
ABORT: Final = b"\x06"
READY: Final = b"\x01"
IN_PROGRESS: Final = b"\x02"
PROTOCOL_V4: Final = b"\x04"

CHUNK_SIZE: Final = 20
DONOR_SIZE: Final = 18_636
DONOR_SHA256: Final = "2f2ac7352776da3b4c952e4c8103e4c5377644468ff17e8fb76bc93bcd19d895"
DONOR_NAME: Final = "BB-278B"

# Relative offsets within the 18,636-byte application stream.
IDENTITY_PATCH_RANGES: Final = ((0x78, 4), (0x80, 2))
KNOWN_IDENTITY_SEEDS: Final = {
    bytes.fromhex("DDD0D39AB40A"),  # verified working donor
    bytes.fromhex("933755985917"),  # OTA-stuck donor
}
