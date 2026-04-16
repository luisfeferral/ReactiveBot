from objects import *
from adb_controller import ControllableDeviceAsync
from random import randint as _randint

adbAction = Action[ControllableDeviceAsync]

@Action.register("tap_ellipse")
class TapEllipseAction[_](adbAction):
    ellipse: Ellipse
    weight: float
    def __init__(self, ellipse_to_tap: Ellipse, weight:float=1) -> None:
        self.ellipse = ellipse_to_tap
        self.weight = weight
    @classmethod
    def from_dict(cls, data):
        e = data["ellipse"]
        kwargs = {}
        if "weight" in data:
            kwargs["weight"] = data["weight"]

        return cls(
            Ellipse(e["x"], e["y"], e["w"], e["h"]),
            **kwargs
        )
    def get_weight(self) -> float:
        return self.weight
    def __str__(self):
        return f"[tap-ellipse] {self.ellipse}"
    async def act(self, device: ControllableDeviceAsync) -> None:
        await device.send_tap(*self.ellipse.get_random_point(), _randint(100, 150))


@Action.register("tap")
class TapAction[_](adbAction):
    position: tuple[int, int]
    time_ms: int
    weight: float
    def __init__(self, position_x:int, position_y:int, time_ms:int, weight:float=1) -> None:
        self.position = position_x, position_y
        self.time_ms = time_ms
        self.weight = weight
    @classmethod
    def from_dict(cls, data):
        pos = data["position"]
        t = data["time_ms"]
        kwargs = {}
        if "weight" in data:
            kwargs["weight"] = data["weight"]

        return cls(
            pos["x"], pos["y"],
            t,
            **kwargs
        )
    def get_weight(self) -> float:
        return self.weight
    def __str__(self):
        return f"[tap] pos: {self.position}; time: {self.time_ms} ms"
    async def act(self, device: ControllableDeviceAsync) -> None:
        await device.send_tap(*self.position, self.time_ms)


@Action.register("button")
class ButtonAction[_](adbAction):
    key_code: int
    key_alias: Optional[str]
    weight: float
    def __init__(self, key_code: int, key_alias:Optional[str]=None, weight:float=1) -> None:
        self.key_code = key_code
        self.key_alias = key_alias
        self.weight = weight
    @classmethod
    def from_dict(cls, data):
        kwargs = {a: v for a, v in data.items() if a in {"key_code", "key_alias", "weight"}}
        return cls(
            **kwargs
        )
    def get_weight(self) -> float:
        return self.weight
    def __str__(self):
        return f"[button] key_code: {self.key_code}"
    def __repr__(self) -> str:
        if self.key_alias is None:
            return self.__str__()
        return f"[button] key: {self.key_alias}; key_code: {self.key_code}"
    async def act(self, device: ControllableDeviceAsync) -> None:
        await device.send_key(self.key_code)
        
        
@Action.register("send_text")
class SendText[_](adbAction):
    text: str
    weight: float
    def __init__(self, text: str, weight:float=1) -> None:
        # Check text is ascii
        if not text.isascii():
            raise ValueError("SendText only can handle ascii strings")
        self.text = text
        self.weight = weight
    @classmethod
    def from_dict(cls, data):
        kwargs = {a: v for a, v in data.items() if a in {"text", "weight"}}
        return cls(
            **kwargs
        )
    def get_weight(self) -> float:
        return self.weight
    def __str__(self):
        return f"[send_text] text: {self.text}"
    async def act(self, device: ControllableDeviceAsync) -> None:
        await device.send_text(self.text)