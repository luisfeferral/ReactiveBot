from enum import Enum, auto
from dataclasses import dataclass
from random import random, randint
from math import sin, cos, pi, sqrt
from abc import ABC, abstractmethod
from typing import Self, Optional
from adbcontroller import ControllableDeviceAsync
import asyncio

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
    
    def __str__(self) -> str:
        return f"x: {self.center_x} ± {self.radius_x}; y: {self.center_y} ± {self.radius_y}"


class Action(ABC):
    @abstractmethod
    def __str__(self) -> str: ...

    @abstractmethod
    async def act(self, device: ControllableDeviceAsync) -> None: ...

    # hashable
    def __hash__(self) -> int:
        return hash(self.__str__())
    def __eq__(self, other: Self) -> bool:
        return self.__str__() == other.__str__()


class WaitAction(Action):
    time_ms: int
    time_s: float
    def __init__(self, time_ms: int) -> None:
        self.time_ms = time_ms
        self.time_s = time_ms / 1000
    def __str__(self):
        return f"[wait] {self.time_ms} ms"
    async def act(self, _device: ControllableDeviceAsync) -> None:
        await asyncio.sleep(self.time_s)


class TapEllipseAction(Action):
    ellipse: Ellipse
    def __init__(self, ellipse_to_tap: Ellipse) -> None:
        self.ellipse = ellipse_to_tap
    def __str__(self):
        return f"[tap-ellipse] {self.ellipse}"
    async def act(self, device: ControllableDeviceAsync) -> None:
        await device.send_tap(*self.ellipse.get_random_point(), randint(100, 150))


class TapAction(Action):
    position: tuple[int, int]
    time_ms: int
    def __init__(self, position_x:int, position_y:int, time_ms:int) -> None:
        self.position = position_x, position_y
        self.time_ms = time_ms
    def __str__(self):
        return f"[tap] pos: {self.position}; time: {self.time_ms} ms"
    async def act(self, device: ControllableDeviceAsync) -> None:
        await device.send_tap(*self.position, self.time_ms)

class ButtonAction(Action):
    key_code: int
    key_alias: Optional[str]
    def __init__(self, key_code: int, key_alias:Optional[str]=None) -> None:
        self.key_code = key_code
        self.key_alias = key_alias
    def __str__(self):
        return f"[button] key_code: {self.key_code}"
    def __repr__(self) -> str:
        if self.key_alias is None:
            return self.__str__()
        return f"[button] key: {self.key_alias}; key_code: {self.key_code}"
    async def act(self, device: ControllableDeviceAsync) -> None:
        await device.send_key(self.key_code)
        

# class PreState:
#     masks: list[png]
#     edges_by_action: dict[Action, str]
#     spontaneous_states: set[str]
#     def __init__(self, masks_strings: list[str], edges: dict[Action, str], spontaneous_states_list: list[str], resolution:tuple[int,int]) -> None:
#         masks = []
#         for m in masks_strings:
#             if m is None:
#                 raise ValueError
#             if resolution:
#                 raise ValueError
#             masks.append(m)
#         edges_by_action = edges
#         spontaneous_states = set(spontaneous_states_list)

class State:
    masks: Optional[list[str]]
    # the set[State] assigned to None is the set with the spontaneous states
    edges_by_action: dict[Optional[Action], set[Self]]
    def __init__(self, masks) -> None:
        self.masks = masks
        self.edges_by_action = {}
    def is_obvious_state(self) -> bool:
        return self.masks is None or len(self.masks) == 0
    def connect(self, action: Optional[Action], edges: set[Self]):
        self.edges_by_action[action] = edges

states_builder = dict[str,
                    tuple[list[str],
                          dict[Optional[Action], list[str]]]]

def load_graph(file: str) -> State:
    # load states from the file
    states:states_builder = {}

    nodes:dict[str, State] = {}
    # 1. Crear nodos
    for reference, (masks, _) in states.items():
        if len(masks) != len(set(masks)):
            # log warning masks dupped in the same state
            # no se usa set porque el orden es importante
            pass
        nodes[reference] = State(
            masks
        )

    # 2. Conectar
    for reference, (_, actions) in states.items():
        for action, edges in actions.items():
            set_edges = set(edges)
            if len(edges) != len(set_edges):
                # log info edges dupped in the same action, dups are removed
                pass
            if len(set_edges) == 0:
                # nodo sin salida, debe cerrar circuitos
                pass
            set_nodes = set(nodes[e] for e in set_edges)
            if sum(n.is_obvious_state() for n in set_nodes) > 1:
                raise SyntaxError("An action can't derive in several states unchecked by masks")
            nodes[reference].connect(action, set_nodes)
        # dentro de cada set no puede haber más de un state sin máscaras

    # 3. Comprobar nodos
    # no puede haber referencias a nodos sin resolver, keyerror en paso 2


    # 4. Comprobar grafo
    # si tiene nodos sin retorno deben ser condiciones para salir de todos los circuitos que se hagan sobre este grafo, avisar
    # no debe haber nodos inalcanzables, no tendrían sentido
    # por lo mismo dos nodos separados pero unidos entre sí tampoco sirven
    nodes_that_can_reach_all = set()
    for reference in states.keys():
        nodes_visited:set[str] = set()
        nodes_to_visit:set[str] = set()
        nodes_to_visit.add(reference)
        while True:
            try:
                edge = nodes_to_visit.pop()
            except KeyError:
                break
            nodes_visited.add(edge)
            if edge in nodes_that_can_reach_all or len(nodes_visited) == len(nodes):
                nodes_that_can_reach_all.add(reference)
                break
            for edges in states[edge][1].values():
                for edge in edges:
                    if edge not in nodes_visited:
                        nodes_to_visit.add(edge)

    return nodes[next(iter(states.keys()))]