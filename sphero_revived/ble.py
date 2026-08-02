from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from bleak import BleakClient, BleakScanner

from .constants import (
    ABORT,
    CHUNK_SIZE,
    COMPLETE,
    DATA_TRANSFER,
    IN_PROGRESS,
    OTA_NAME,
    OTA_SERVICE,
    OTA_VERSION,
    PROTOCOL_V4,
    READY,
    START,
    TRANSFER_CONTROL,
)


@dataclass(frozen=True)
class Advertisement:
    address: str
    name: str
    rssi: int | None


def log(message: str = "") -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


async def scan(timeout: float = 20.0) -> list[Advertisement]:
    found: dict[str, Advertisement] = {}

    def callback(device, advertisement_data) -> None:
        name = advertisement_data.local_name or device.name or "<unnamed>"
        found[device.address.upper()] = Advertisement(
            address=device.address,
            name=name,
            rssi=getattr(advertisement_data, "rssi", None),
        )

    scanner = BleakScanner(callback)
    await scanner.start()
    await asyncio.sleep(timeout)
    await scanner.stop()
    return list(found.values())


async def find_ota_device(address: str | None, timeout: float = 25.0):
    selected = None

    def callback(device, advertisement_data) -> None:
        nonlocal selected
        name = advertisement_data.local_name or device.name or ""
        if address and device.address.upper() == address.upper():
            selected = device
        elif not address and name.strip().upper() == OTA_NAME:
            selected = device

    scanner = BleakScanner(callback)
    await scanner.start()
    deadline = asyncio.get_running_loop().time() + timeout
    while selected is None and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.2)
    await scanner.stop()
    if selected is None:
        target = address or OTA_NAME
        raise RuntimeError(f"Could not find OTA device: {target}")
    return selected


async def visible_bb_devices(timeout: float = 8.0) -> list[Advertisement]:
    return [item for item in await scan(timeout) if item.name.upper().startswith("BB-")]


async def transfer_image(
    image: bytes,
    ota_address: str | None,
    progress: Callable[[int, int, float], None],
) -> dict:
    device = await find_ota_device(ota_address)
    disconnected = asyncio.Event()
    notifications: list[bytes] = []
    started = False
    completed = False

    def on_disconnect(_client: BleakClient) -> None:
        disconnected.set()
        log("BB-8 disconnected.")

    def on_status(_characteristic, data: bytearray) -> None:
        payload = bytes(data)
        notifications.append(payload)
        log(f"1015 notification: {payload.hex(' ').upper()}")

    client = BleakClient(device, timeout=60.0, disconnected_callback=on_disconnect)
    try:
        log(f"Connecting to {device.name or OTA_NAME} at {device.address}...")
        await client.connect()
        if client.services.get_service(OTA_SERVICE) is None:
            raise RuntimeError("CSR OTA service 1010 is absent.")

        await client.start_notify(TRANSFER_CONTROL, on_status)
        await asyncio.sleep(0.7)
        version = bytes(await client.read_gatt_char(OTA_VERSION))
        state = bytes(await client.read_gatt_char(TRANSFER_CONTROL))
        if version != PROTOCOL_V4:
            raise RuntimeError(f"Unsupported CSR OTA protocol: {version.hex()}")
        if state != READY:
            raise RuntimeError(f"OTA device is not READY: {state.hex()}")

        log("Sending START (02)...")
        await client.write_gatt_char(TRANSFER_CONTROL, START, response=True)
        started = True

        for _ in range(70):
            if IN_PROGRESS in notifications:
                break
            if disconnected.is_set():
                raise RuntimeError("Disconnected before IN_PROGRESS was confirmed.")
            await asyncio.sleep(0.1)

        state = bytes(await client.read_gatt_char(TRANSFER_CONTROL))
        if state != IN_PROGRESS:
            raise RuntimeError(f"Expected IN_PROGRESS 02, got {state.hex()}.")

        sent = 0
        start_time = time.monotonic()
        while sent < len(image):
            chunk = image[sent : sent + CHUNK_SIZE]
            await client.write_gatt_char(DATA_TRANSFER, chunk, response=True)
            sent += len(chunk)
            progress(sent, len(image), max(time.monotonic() - start_time, 0.001))

        log("Every byte was accepted. Sending COMPLETE (04)...")
        await client.write_gatt_char(TRANSFER_CONTROL, COMPLETE, response=True)
        completed = True

        try:
            await asyncio.wait_for(disconnected.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            log("No reboot disconnect was observed within 30 seconds.")

        return {
            "ota_address": device.address,
            "protocol": version.hex().upper(),
            "initial_state": "01",
            "bytes_sent": len(image),
            "complete_accepted": completed,
            "notifications": [item.hex().upper() for item in notifications],
        }
    except Exception:
        if started and not completed and client.is_connected:
            try:
                log("Attempting official ABORT (06)...")
                await client.write_gatt_char(TRANSFER_CONTROL, ABORT, response=True)
            except Exception as abort_error:
                log(f"ABORT failed: {type(abort_error).__name__}: {abort_error}")
        raise
    finally:
        if client.is_connected:
            try:
                await client.stop_notify(TRANSFER_CONTROL)
            except Exception:
                pass
            try:
                await client.disconnect()
            except Exception:
                pass
