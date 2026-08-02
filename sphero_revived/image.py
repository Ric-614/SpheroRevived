from __future__ import annotations

import hashlib
import secrets
import struct
from dataclasses import asdict, dataclass

from .constants import (
    DONOR_SHA256,
    DONOR_SIZE,
    IDENTITY_PATCH_RANGES,
    KNOWN_IDENTITY_SEEDS,
)
from .crc import csr_crc16


@dataclass(frozen=True)
class ControlBlock:
    index: int
    offset: int
    destination: int
    length: int
    stored_crc: int
    calculated_crc: int

    @property
    def valid(self) -> bool:
        return self.stored_crc == self.calculated_crc


@dataclass(frozen=True)
class Validation:
    sha256: str
    size: int
    block_count: int
    stream_length: int
    control_crc_stored: int
    control_crc_calculated: int
    blocks: tuple[ControlBlock, ...]

    @property
    def valid(self) -> bool:
        return (
            self.control_crc_stored == self.control_crc_calculated
            and self.stream_length == self.size
            and all(block.valid for block in self.blocks)
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["valid"] = self.valid
        data["blocks"] = [
            {**asdict(block), "valid": block.valid} for block in self.blocks
        ]
        return data


def _word(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def validate_image(data: bytes) -> Validation:
    if len(data) < 16:
        raise ValueError("Image is too short to contain a CSR control header.")

    block_count = (_word(data, 2) >> 8) & 0xFF
    if block_count == 0 or block_count > 32:
        raise ValueError(f"Implausible CSR control-block count: {block_count}")

    header_end = 6 + block_count * 8
    if header_end > len(data):
        raise ValueError("CSR control header extends beyond the image.")

    blocks: list[ControlBlock] = []
    stream_length = 0
    for index in range(block_count):
        descriptor = 6 + index * 8
        offset, destination, length, stored_crc = struct.unpack_from(
            "<HHHH", data, descriptor
        )
        end = offset + length
        if end > len(data):
            raise ValueError(
                f"Block {index} extends beyond image: 0x{end:04X} > 0x{len(data):04X}"
            )
        calculated = csr_crc16(data[offset:end])
        blocks.append(
            ControlBlock(
                index=index,
                offset=offset,
                destination=destination,
                length=length,
                stored_crc=stored_crc,
                calculated_crc=calculated,
            )
        )
        stream_length = max(stream_length, end)

    stored_control = _word(data, 0)
    calculated_control = csr_crc16(data[2:header_end])
    return Validation(
        sha256=hashlib.sha256(data).hexdigest(),
        size=len(data),
        block_count=block_count,
        stream_length=stream_length,
        control_crc_stored=stored_control,
        control_crc_calculated=calculated_control,
        blocks=tuple(blocks),
    )


def verify_pristine_donor(data: bytes) -> Validation:
    digest = hashlib.sha256(data).hexdigest()
    if len(data) != DONOR_SIZE or digest != DONOR_SHA256:
        raise ValueError(
            "Bundled donor firmware does not match the verified release image. "
            "Refusing to continue."
        )
    validation = validate_image(data)
    if not validation.valid:
        raise ValueError("Bundled donor image failed CSR integrity validation.")
    return validation


def generate_identity_seed() -> bytes:
    while True:
        seed = secrets.token_bytes(6)
        if seed in KNOWN_IDENTITY_SEEDS:
            continue
        if seed in (b"\x00" * 6, b"\xFF" * 6):
            continue
        if len(set(seed)) == 1:
            continue
        return seed


def read_identity_seed(data: bytes) -> bytes:
    return b"".join(data[offset : offset + length] for offset, length in IDENTITY_PATCH_RANGES)


def build_experimental_image(donor: bytes, seed: bytes) -> tuple[bytes, dict]:
    if len(seed) != 6:
        raise ValueError("Identity candidate must be exactly six bytes.")
    verify_pristine_donor(donor)

    patched = bytearray(donor)
    old_seed = read_identity_seed(donor)
    cursor = 0
    changed_offsets: list[dict] = []
    for offset, length in IDENTITY_PATCH_RANGES:
        before = bytes(patched[offset : offset + length])
        after = seed[cursor : cursor + length]
        patched[offset : offset + length] = after
        changed_offsets.append(
            {
                "offset": offset,
                "length": length,
                "before": before.hex().upper(),
                "after": after.hex().upper(),
            }
        )
        cursor += length

    # Recalculate each block CRC. This is intentionally generic rather than
    # hard-coding which block contains the patched identity bytes.
    block_count = (_word(patched, 2) >> 8) & 0xFF
    for index in range(block_count):
        descriptor = 6 + index * 8
        offset, _destination, length, _stored = struct.unpack_from(
            "<HHHH", patched, descriptor
        )
        new_crc = csr_crc16(bytes(patched[offset : offset + length]))
        struct.pack_into("<H", patched, descriptor + 6, new_crc)

    # Descriptor CRC fields changed, so rebuild the control-header CRC last.
    header_end = 6 + block_count * 8
    struct.pack_into("<H", patched, 0, csr_crc16(bytes(patched[2:header_end])))

    result = bytes(patched)
    validation = validate_image(result)
    if not validation.valid:
        raise RuntimeError("Generated experimental image failed independent validation.")

    # Enforce the one-variable design: only identity bytes and integrity fields
    # are allowed to differ from the immutable donor.
    allowed = set()
    for offset, length in IDENTITY_PATCH_RANGES:
        allowed.update(range(offset, offset + length))
    allowed.update((0, 1))  # control-header CRC
    for index in range(block_count):
        descriptor_crc = 6 + index * 8 + 6
        allowed.update((descriptor_crc, descriptor_crc + 1))

    unexpected = [
        index
        for index, (left, right) in enumerate(zip(donor, result))
        if left != right and index not in allowed
    ]
    if unexpected:
        raise RuntimeError(
            "Experimental builder changed bytes outside approved identity/integrity fields: "
            + ", ".join(f"0x{x:04X}" for x in unexpected[:20])
        )

    manifest = {
        "base_sha256": hashlib.sha256(donor).hexdigest(),
        "base_identity_seed": old_seed.hex().upper(),
        "generated_identity_seed": seed.hex().upper(),
        "changed_identity_ranges": changed_offsets,
        "result_sha256": hashlib.sha256(result).hexdigest(),
        "validation": validation.to_dict(),
        "hardware_status": "UNTESTED",
        "claim": (
            "Structurally valid CSR application image with modified identity-related bytes. "
            "The resulting BLE identity and boot behavior cannot be predicted."
        ),
    }
    return result, manifest
