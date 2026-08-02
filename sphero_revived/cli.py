from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

from . import __version__
from .ble import Advertisement, log, scan, transfer_image, visible_bb_devices
from .constants import DONOR_NAME
from .image import (
    build_experimental_image,
    generate_identity_seed,
    verify_pristine_donor,
)
from .report import add_event, new_report, save_report


import os


def bundled_root() -> Path:
    """
    Source checkout:
        project root

    PyInstaller one-file build:
        temporary _MEI extraction directory
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def user_data_root() -> Path:
    """
    Persistent writable storage for reports and experiments.
    """
    if sys.platform == "win32":
        base = Path(
            os.environ.get(
                "LOCALAPPDATA",
                Path.home() / "AppData" / "Local",
            )
        )
        return base / "SpheroRevived"

    base = Path(
        os.environ.get(
            "XDG_DATA_HOME",
            Path.home() / ".local" / "share",
        )
    )
    return base / "SpheroRevived"


BUNDLED_ROOT = bundled_root()
USER_DATA_ROOT = user_data_root()

DEFAULT_FIRMWARE = (
    BUNDLED_ROOT
    / "firmware"
    / "bb8"
    / "working_donor_application.bin"
)

DEFAULT_REPORTS = USER_DATA_ROOT / "reports"
DEFAULT_EXPERIMENTS = USER_DATA_ROOT / "experiments"


def ask_exact(prompt: str, expected: str) -> None:
    typed = input(f'{prompt}\nType exactly "{expected}" to continue: ').strip()
    if typed != expected:
        raise RuntimeError("Confirmation did not match. Cancelled safely.")


def print_safety() -> None:
    print(
        """
Before recovery:
  • Put BB-8 in its stable, motionless OTA UPDATE state.
  • Keep it centered on a powered charger.
  • Do not press the charger button during transfer.
  • Prevent this computer from sleeping or suspending.
  • Keep the Bluetooth adapter close to the droid.
""".strip()
    )


def progress(sent: int, total: int, elapsed: float) -> None:
    if sent == total or sent % 1000 < 20:
        percent = sent * 100.0 / total
        speed = sent / elapsed
        log(f"Progress: {sent}/{total} bytes ({percent:.1f}%), {speed:.0f} B/s")


def summarize_devices(devices: list[Advertisement]) -> None:
    if not devices:
        print("No BB- devices detected.")
        return
    for device in sorted(devices, key=lambda item: item.name):
        rssi = "n/a" if device.rssi is None else str(device.rssi)
        print(f"  {device.name:<12} {device.address:<20} RSSI {rssi}")


async def post_recovery_scan(before: list[Advertisement]) -> dict:
    before_addresses = {device.address.upper() for device in before}
    before_pairs = {(device.address.upper(), device.name.upper()) for device in before}
    observed: dict[str, Advertisement] = {}

    log("Waiting 6 seconds before post-reboot discovery...")
    await asyncio.sleep(6.0)
    for attempt in range(1, 4):
        log(f"Scanning for restored BB-8 (attempt {attempt}/3)...")
        for device in await visible_bb_devices(timeout=10.0):
            observed[device.address.upper()] = device
        if any(
            device.address.upper() not in before_addresses
            or (device.address.upper(), device.name.upper()) not in before_pairs
            for device in observed.values()
        ):
            break
        await asyncio.sleep(3.0)

    devices = list(observed.values())
    new_devices = [
        device
        for device in devices
        if device.address.upper() not in before_addresses
        or (device.address.upper(), device.name.upper()) not in before_pairs
    ]
    return {
        "all_bb_devices": [device.__dict__ for device in devices],
        "new_bb_devices": [device.__dict__ for device in new_devices],
    }


async def run_recovery(
    mode: str,
    firmware_path: Path,
    ota_address: str | None,
    reports_dir: Path,
    experiments_dir: Path,
) -> int:
    donor = firmware_path.read_bytes()
    donor_validation = verify_pristine_donor(donor)
    report = new_report(mode, __version__)
    report["donor"] = donor_validation.to_dict()
    add_event(report, "donor_verified", sha256=donor_validation.sha256)

    image = donor
    experiment_id = None
    if mode == "experimental":
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        experiment_id = f"EXP-{timestamp}"
        seed = generate_identity_seed()
        image, manifest = build_experimental_image(donor, seed)
        experiments_dir.mkdir(parents=True, exist_ok=True)
        image_path = experiments_dir / f"{experiment_id}.bin"
        manifest_path = experiments_dir / f"{experiment_id}.json"
        image_path.write_bytes(image)
        manifest["experiment_id"] = experiment_id
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        report["experiment"] = manifest
        add_event(
            report,
            "experimental_image_built",
            experiment_id=experiment_id,
            image_sha256=hashlib.sha256(image).hexdigest(),
            seed=seed.hex().upper(),
        )
        print(f"Experiment ID: {experiment_id}")
        print(f"Generated identity candidate: {seed.hex(' ').upper()}")
        print(f"Archived image: {image_path}")
        print(f"Archived manifest: {manifest_path}")

    log("Recording BB- devices visible before recovery...")
    before = await visible_bb_devices(timeout=6.0)
    report["pre_recovery_bb_devices"] = [device.__dict__ for device in before]

    transfer = await transfer_image(image, ota_address, progress)
    report["transfer"] = transfer
    add_event(report, "transfer_completed", bytes_sent=len(image))

    discovery = await post_recovery_scan(before)
    report["post_recovery_discovery"] = discovery
    new_devices = discovery["new_bb_devices"]

    if new_devices:
        detected = new_devices[0]
        print("\nRecovery transfer completed and a restored BB-8 was detected:")
        print(f"  Name:    {detected['name']}")
        print(f"  Address: {detected['address']}")
        print("\nOpen Sphero Edu, select BB-8, and connect to that name.")
        print("Allow the official firmware update to finish if prompted.")
        report["outcome"] = "restored_bb8_detected"
        report["detected_device"] = detected
        add_event(report, "restored_bb8_detected", **detected)
    else:
        print("\nThe image transfer completed, but no restored BB-8 was detected.")
        if mode == "experimental":
            print("\nAvailable next steps:")
            print("  1. Retry Experimental Recovery with a new identity candidate.")
            print(f"  2. Run Stable Recovery to restore the verified {DONOR_NAME} image.")
        else:
            print("Wait briefly, scan again, then check Sphero Edu for BB-278B.")
        report["outcome"] = "transfer_complete_no_bb_detected"
        add_event(report, "no_restored_bb8_detected")

    stem = experiment_id or f"stable-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    report_path = save_report(report, reports_dir, stem)
    print(f"\nSaved recovery report: {report_path}")
    return 0


async def diagnose() -> int:
    print("Scanning for nearby devices for 15 seconds...")
    devices = await scan(15.0)
    ota = [device for device in devices if device.name.upper() == "OTA UPDATE"]
    bb = [device for device in devices if device.name.upper().startswith("BB-")]
    print("\nOTA UPDATE devices:")
    summarize_devices(ota)
    print("\nNormal BB- devices:")
    summarize_devices(bb)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sphero-revived")
    parser.add_argument("--firmware", type=Path, default=DEFAULT_FIRMWARE)
    parser.add_argument("--ota-address", help="Optional OTA UPDATE BLE address")
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS)
    parser.add_argument("--experiments-dir", type=Path, default=DEFAULT_EXPERIMENTS)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("diagnose", help="read-only device scan")
    sub.add_parser("stable", help="verified donor recovery")
    sub.add_parser("experimental", help="untested randomized identity recovery")
    return parser


def interactive_choice() -> str:
    print(
        f"""
Sphero Revived {__version__}
Reviving the Fun, One Sphero at a Time.

1. Diagnose / scan only
2. Stable BB-8 Recovery (verified; restores {DONOR_NAME})
3. Experimental randomized identity recovery (UNTESTED)
4. Exit
""".strip()
    )
    return input("\nChoose an option: ").strip()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    command = args.command
    if command is None:
        choice = interactive_choice()
        command = {"1": "diagnose", "2": "stable", "3": "experimental", "4": "exit"}.get(choice)
        if command is None:
            print("Invalid choice.")
            return 2

    if command == "exit":
        return 0
    if command == "diagnose":
        return asyncio.run(diagnose())

    print_safety()
    if command == "stable":
        print(
            f"\nStable Recovery uses the exact hardware-verified donor image and "
            f"should restore the droid as {DONOR_NAME}."
        )
        ask_exact("This is a real firmware-writing operation.", "RESTORE BB-8")
    elif command == "experimental":
        print(
            """
EXPERIMENTAL — NOT HARDWARE VERIFIED

This mode copies the immutable donor image, changes only six identity-related
bytes, rebuilds every dependent CSR CRC, validates the result, and flashes the
new copy. The resulting name/address cannot be predicted. The application may
fail to boot. Stable Recovery remains the verified fallback only if OTA UPDATE
is still available afterward; that fallback cannot be guaranteed until this
experimental path has been tested on hardware.
""".strip()
        )
        ask_exact(
            "Proceed only if you understand the experimental risk.",
            "I ACCEPT THE EXPERIMENTAL RISK",
        )

    try:
        return asyncio.run(
            run_recovery(
                command,
                args.firmware,
                args.ota_address,
                args.reports_dir,
                args.experiments_dir,
            )
        )
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except Exception as error:
        print(f"\nERROR: {type(error).__name__}: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
