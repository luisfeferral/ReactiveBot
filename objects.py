from enum import Enum, auto
from dataclasses import dataclass
from random import random
from math import sin, cos, pi, sqrt

from ppadb.client_async import ClientAsync
from ppadb.device_async import DeviceAsync
import yaml
from yaml.parser import ParserError
@dataclass
class Ellipse:
    center_x: int
    center_y: int
    radius_x: int
    radius_y: int

    def get_random_point(self) -> tuple[int, int]:
        # Vamos a calcular un punto aleatorio en un circulo unitario y luego lo pasamos a la elipse
        # Tomamos un ángulo aleatorio
        theta = random() * 2 * pi

        # La raíz cuadrada compensa la diferencia de área que hay cerca del centro y en los bordes
        r = sqrt(random())

        # Punto en círculo unitario
        u = r * cos(theta)
        v = r * sin(theta)

        # Escalado a la elipse
        x = self.center_x + u * self.radius_x
        y = self.center_y + v * self.radius_y

        return int(x), int(y)

class TypeAction(Enum):
    WAIT = auto()
    TAP_ELLIPSE = auto()
    TAP = auto()
    PULSE = auto()
    BUTTON = auto()
    DRAG = auto()

class Action:
    # click, drag, wait, button, write/copy/paste?
    type: TypeAction
    args: tuple[str|int, ...]
    # hasheable
    def __init__(self, type:TypeAction, *args:str|int) -> None:
        if type == TypeAction.WAIT: # ms
            if len(args) != 1 and any(not isinstance(a,(int, float)) for a in args):
                raise ValueError
            # build the action method
        
        elif type == TypeAction.TAP_ELLIPSE: # ellipse
            if len(args) != 2 and any(not isinstance(a, Ellipse) for a in args):
                raise ValueError
            # build the action method
            
        elif type == TypeAction.TAP: # x, y
            if len(args) != 2 and any(not isinstance(a, int) for a in args):
                raise ValueError
            # build the action method

        elif type == TypeAction.PULSE: # x, y, ms
            if len(args) != 3 and any(not isinstance(a, int) for a in args):
                raise ValueError
            # build the action method

        elif type == TypeAction.BUTTON: # button
            if len(args) != 1 and any(not isinstance(a, int) for a in args):
                raise ValueError
            # build the action method
            
            input swipe 1 1 2 2 100
        


class PreState:
    masks: list[png]
    edges_by_action: dict[Action, str]
    spontaneous_states: set[str]
    def __init__(self, masks_strings: list[str], edges: dict[Action, str], spontaneous_states_list: list[str], resolution:tuple[int,int]) -> None:
        masks = []
        for m in masks_strings:
            if m is None:
                raise ValueError
            if resolution:
                raise ValueError
            masks.append(m)
        edges_by_action = edges
        spontaneous_states = set(spontaneous_states_list)

class State:
    masks: list[png]
    edges_by_action: dict[Action, State]
    spontaneous_states: set[State]