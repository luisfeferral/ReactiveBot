from ppadb.client_async import ClientAsync
from ppadb.device_async import DeviceAsync
import io
from typing import IO
import logging
from objects import CapturableDevice

logger = logging.getLogger(__name__)

class ControllableDeviceAsync(DeviceAsync, CapturableDevice):
    def __init__(self, client, serial, debugging_image="last_screencap.png"):
        super().__init__(client, serial)
        self.debugging_image = debugging_image

    async def save_image(self, img_file: str) -> bool:
        try:
            byte_array: bytearray = await self.screencap()
            with open(img_file, "wb") as f:
                f.write(byte_array)
            return True
        except:
            return False

    async def get_image(self) -> IO[bytes]:
        byte_array: bytearray = await self.screencap()
        byte_stream = io.BytesIO(bytes(byte_array))
        byte_stream.seek(0)
        if not byte_array.startswith(b'\x89PNG'):
            logger.warning(f"The image obtained by the device {self.serial} doesn't seem like a valid PNG")
        if logger.isEnabledFor(logging.DEBUG):
            with open(self.debugging_image, "wb") as f:
                f.write(byte_array)
        return byte_stream

    async def send_tap(self, x, y, ms_duration) -> None:
        # ms_duration = int(1000 * duration)
        if ms_duration == 0:
            await self.shell(f'input tap {x} {y}')
            logger.info(f"[send_tap] Tap in ({x},{y})")
        else:
            await self.shell(f'input swipe {x} {y} {x} {y} {ms_duration}')
            logger.info(f"[send_tap] Tap in ({x},{y}) dur={ms_duration}ms")


    async def send_swipe(self, x_0, y_0, x_1, y_1, ms_duration):
        await self.shell(f'input swipe {x_0} {y_0} {x_1} {y_1} {ms_duration}')
        logger.info(f"[send_swipe] Swipe from ({x_0},{y_0}) to ({x_1},{y_1}) dur={ms_duration}ms")


    async def send_drag(self, points):
        logger.info(f"[send_drag] Sent drag with {len(points)} points")


    async def send_text(self, text: str):
        # Text str must be ascii
        await self.shell(f"input text '{text.replace(" ", "%s")}'")
        logger.info("[send_text] Sent text:", text.replace(" ", "%s"))


    async def send_key(self, key_code: int):
        await self.shell(f'input keyevent {key_code}')
        logger.info(f"[send_key] Key:", key_code)


async def select_and_load_device() -> ControllableDeviceAsync:
    '''Prints the list of devices connected and wait the user returns the option wants to select'''
    client = ClientAsync()
    devices: list[DeviceAsync] = await client.devices()
    if not devices:
        raise ValueError('No devices found')
    print('Found devices:')
    for device in devices:
        print(' ', device.serial)
    for device in devices:
        response = input(f"Would you like to load this device ({device.serial})? ")
        while response.lower() not in {"si", "s", "no", "n", "yes", "y"}:
            response = input(f"Would you like to load this device ({device.serial})? ")
        if response.lower() in {"no", "n"}:
            continue
        else:
            return ControllableDeviceAsync(device.client, device.serial)
    
    raise ValueError(f'No devices selected')

async def load_device(serial: str) -> ControllableDeviceAsync:
    client = ClientAsync()
    devices: list[DeviceAsync] = await client.devices()
    if not devices:
        raise ValueError('No devices found')
    for device in devices:
        if serial == device.serial:
            return ControllableDeviceAsync(device.client, device.serial)
    
    print('Found devices:')
    for device in devices:
        print(' ', device.serial)
    raise ValueError(f'Device {serial} not found')