from __future__ import annotations


def _reflect8(value: int) -> int:
    return int(f"{value:08b}"[::-1], 2)


def _make_table() -> tuple[int, ...]:
    table: list[int] = []
    for dividend in range(256):
        remainder = dividend << 8
        for _ in range(8):
            if remainder & 0x8000:
                remainder = ((remainder << 1) ^ 0x8005) & 0xFFFF
            else:
                remainder = (remainder << 1) & 0xFFFF
        table.append(remainder)
    return tuple(table)


_TABLE = _make_table()


def csr_crc16(data: bytes) -> int:
    remainder = 0
    for byte in data:
        index = (_reflect8(byte) ^ ((remainder >> 8) & 0xFF)) & 0xFF
        remainder = (_TABLE[index] ^ ((remainder << 8) & 0xFFFF)) & 0xFFFF
    return remainder
