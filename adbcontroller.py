from ppadb.client_async import ClientAsync
from ppadb.device_async import DeviceAsync
import io


class ControllableDeviceAsync(DeviceAsync):
    def __init__(self, client, serial):
        super().__init__(client, serial)

    async def get_image(self) -> io.BytesIO:
        byte_array: bytearray = await self.screencap()
        byte_stream = io.BytesIO(bytes(byte_array))
        byte_stream.seek(0)
        return byte_stream

    async def send_tap(self, x, y, ms_duration) -> None:
        # ms_duration = int(1000 * duration)
        if ms_duration == 0:
            await self.shell(f'input tap {x} {y}')
            print(f"[send_tap] Tap en ({x},{y})")
        else:
            await self.shell(f'input swipe {x} {y} {x} {y} {ms_duration}')
            print(f"[send_tap] Tap en ({x},{y}) dur={ms_duration}ms")


    def send_drag(self, points):
        print(f"[send_drag] Drag con {len(points)} puntos")


    async def send_text(self, text: str):
        # No funciona bien para cosas unicode creo
        await self.shell(f"input text '{text.replace(" ", "%s")}'")
        print("[send_text] Texto enviado:", text.replace(" ", "%s"))


    async def send_key(self, key_code: int):
        await self.shell(f'input keyevent {key_code}')
        print(f"[send_key] Tecla:", key_code)