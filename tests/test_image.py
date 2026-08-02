from pathlib import Path

from sphero_revived.image import (
    build_experimental_image,
    read_identity_seed,
    validate_image,
    verify_pristine_donor,
)

ROOT = Path(__file__).resolve().parents[1]
DONOR = ROOT / "firmware" / "bb8" / "working_donor_application.bin"


def test_verified_donor():
    data = DONOR.read_bytes()
    assert verify_pristine_donor(data).valid
    assert read_identity_seed(data).hex().upper() == "DDD0D39AB40A"


def test_experimental_builder_is_valid_and_preserves_donor():
    donor = DONOR.read_bytes()
    candidate, manifest = build_experimental_image(donor, bytes.fromhex("123456789ABC"))
    assert donor == DONOR.read_bytes()
    assert candidate != donor
    assert validate_image(candidate).valid
    assert manifest["generated_identity_seed"] == "123456789ABC"
