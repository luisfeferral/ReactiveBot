from __future__ import annotations

from dataclasses import dataclass
from random import random, randint
from math import sin, cos, pi, sqrt
from abc import ABC, abstractmethod
from typing import Any, Optional
from adbcontroller import ControllableDeviceAsync, TestingDevice
import asyncio
import numpy as np
from PIL import Image
import json
import pathlib

class Mask:
    _rgb_array: np.ndarray
    _filtered_array: np.ndarray
    _dimensions: tuple[int, int]
    def __init__(self, img_source) -> None:
        img = np.array(Image.open(img_source).convert("RGBA"))
        self._rgb_array = img[:, :, :3]
        self._dimensions = self._rgb_array.shape[:2]
        self._filtered_array = img[:, :, 3] >= 128 # / 255
    def mask_match(self, img: np.ndarray) -> bool:
        img_rgb = img[:, :, :3]
        if self._dimensions != img_rgb.shape:
            return False
        return bool(np.all(self._rgb_array[self._filtered_array] == img_rgb[self._filtered_array]))


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
    registry = {}

    @classmethod
    def register(cls, action_type):
        def decorator(subclass):
            cls.registry[action_type] = subclass
            return subclass
        return decorator

    @classmethod
    def from_dict(cls, data) -> Action:
        action_type = data["type"]
        subclass = cls.registry[action_type]
        return subclass.from_dict(data)
    
    @abstractmethod
    def __str__(self) -> str: ...

    def __repr__(self) -> str:
        return self.__str__()

    @abstractmethod
    async def act(self, device: ControllableDeviceAsync) -> None: ...

    @abstractmethod
    def get_weight(self) -> float: ...

    def get_actions(self) -> list[Action]: 
        return [self]

    def __add__(self, other: Any) -> MacroAction:
        if isinstance(other, int):
            return self + WaitAction(other)
        elif isinstance(other, Action):
            return MacroAction(self.get_actions() + other.get_actions())
        raise NotImplemented
    # hashable
    def __hash__(self) -> int:
        return hash(self.__str__())
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Action):
            return NotImplemented
        return str(self) == str(other)


@Action.register("macro")
class MacroAction(Action):
    actions: list[Action]
    def __init__(self, actions: list[Action]) -> None:
        self.actions = actions
    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        actions = data["actions"]
        return cls(
            list(Action.from_dict(a) for a in actions)
        )
    def get_weight(self) -> float:
        return sum(action.get_weight() for action in self.actions)
    def __str__(self):
        return f"[macro]: ({' + '.join(str(a) for a in self.actions)})"
    async def act(self, device: ControllableDeviceAsync) -> None:
        for a in self.actions:
            await a.act(device)
    def get_actions(self) -> list[Action]:
        return self.actions


@Action.register("wait")
class WaitAction(Action):
    time_ms: int
    time_s: float
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    def __init__(self, time_ms: int) -> None:
        self.time_ms = time_ms
        self.time_s = time_ms / 1000
    def get_weight(self) -> float:
        return self.time_s
    def __str__(self):
        return f"[wait] {self.time_ms} ms"
    async def act(self, _device: ControllableDeviceAsync) -> None:
        await asyncio.sleep(self.time_s)


@Action.register("tap_ellipse")
class TapEllipseAction(Action):
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
        await device.send_tap(*self.ellipse.get_random_point(), randint(100, 150))


@Action.register("tap")
class TapAction(Action):
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
class ButtonAction(Action):
    key_code: int
    key_alias: Optional[str]
    weight: float
    def __init__(self, key_code: int, key_alias:Optional[str]=None, weight:float=1) -> None:
        self.key_code = key_code
        self.key_alias = key_alias
        self.weight = weight
    @classmethod
    def from_dict(cls, data):
        return cls(
            **data
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


class State:
    alias: str
    masks: Optional[list[Mask]]
    # the set[State] assigned to None is the set with the spontaneous states
    edges_by_action: dict[Optional[Action], set[State]]
    def __init__(self, alias: str, masks: Optional[list[Mask]]) -> None:
        self.alias = alias
        self.masks = masks
        self.edges_by_action = {}
    def get_name(self):
        return self.alias
    def __repr__(self) -> str:
        return f"[State] {self.alias}"
    def is_obvious_state(self) -> bool:
        return self.masks is None or len(self.masks) == 0
    def can_be_in_this_state(self, screen_img: np.ndarray) -> bool:
        if self.masks is None or len(self.masks) == 0:
            return True
        return any(m.mask_match(screen_img) for m in self.masks)
    def connect(self, action: Optional[Action], edges: set[State]):
        self.edges_by_action[action] = edges

states_builder = dict[str,
                    tuple[list[str],
                          dict[Optional[Action], list[str]]]]

def load_graph(json_path: str) -> dict[Optional[str], State]:
    # load states from the file
    states:states_builder = {}

    path = pathlib.Path(json_path).parent

    with open(json_path) as f:
        data = json.load(f)

    states = {}

    for state_id, state_data in data["states"].items():
        masks = state_data["masks"]
        transitions = {}

        for t in state_data["transitions"]:
            if t["action"] is None:
                transitions[None] = t["next_states"]
            else:
                action = Action.from_dict(t["action"])
                transitions[action] = t["next_states"]

        states[state_id] = (masks, transitions)


    nodes:dict[Optional[str], State] = {}
    # 1. Crear nodos
    for reference, (masks, _) in states.items():
        if len(masks) != len(set(masks)):
            # log warning masks dupped in the same state
            # no se usa set porque el orden es importante
            pass
        nodes[reference] = State(
            reference,
            [Mask(str(path/m)) for m in masks] if masks else None
        ) # cuidado porque lo lógico sería que las rutas de las máscaras sean relativas a su archivo

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
    nodes[None] = nodes[next(iter(states.keys()))] # Initial state
    return nodes

def calculate_shortest_path(states_dict:dict[Optional[str],State], actual_state: str, target_state: str, weight_spontaneous_actions:float=5) -> list[str]:
    # Uses Dijkstra for get the shorthest distance, but returns the path

    shortest: dict[str, tuple[float, Optional[str]]] = {}
    explored: set[str] = set()

    shortest[actual_state] = (0, None)

    while target_state not in shortest:
        estimated = None
        for edge, (estimated_weight, _) in shortest.items():
            if edge not in explored and (estimated is None or estimated_weight < estimated):
                actual_node = edge
                estimated = estimated_weight
        if estimated is None:
            raise ValueError("The target state is unreachable")

        for action, edges in states_dict[actual_node].edges_by_action.items():
            estimated += weight_spontaneous_actions if action is None else action.get_weight()
            for edge in edges:
                name_edge = edge.alias
                if name_edge not in shortest or shortest[name_edge][0] > estimated:
                    shortest[name_edge] = (estimated, actual_node)
            estimated -= weight_spontaneous_actions if action is None else action.get_weight()
        explored.add(actual_node)

    route = [target_state]
    previous_node = actual_node
    while previous_node != actual_state:
        assert previous_node is not None
        actual_node = previous_node
        route.append(previous_node)
        previous_node = shortest[actual_node][1]
    return route

        

async def complete_task(device: ControllableDeviceAsync, states_dict:dict[Optional[str],State], target: tuple[str, str], limits_loop: dict[tuple[str,str],int]):
    # target = "edge_name1" -> "edge_name2"
    # if the goal is reach the target a limited number of times, the goal_reach can be restricted in the limits
    edges_traveled: dict[tuple[str,str], int] = {}

    weight_spontaneous_actions = 5

    def in_limits(edges_traveled: dict[tuple[str,str], int], limits: dict[tuple[str,str], int]):
        for k, v in edges_traveled.items():
            if k in limits and v >= limits[k]:
                return False
        return True
    
    route = []
    actual_state = states_dict[None]
    while in_limits(edges_traveled, limits_loop):
        possible_states: set[State] = set()
        if actual_state.alias == target[0]:
            for action, edges in actual_state.edges_by_action.items():
                if states_dict[target[1]] in edges:
                    action_selected = action
                    possible_states = possible_states.union(edges)
                    break
            if isinstance(device, TestingDevice):
                print(f"Trying to go to {target[1]}, making {action_selected}")
        else:
            if len(route) > 1 and route[-1] == actual_state.alias:
                route.pop()
            else:
                route = calculate_shortest_path(states_dict, actual_state.alias, target[0], weight_spontaneous_actions)
                if isinstance(device, TestingDevice):
                    print(f"Recalculated route. New route: {route}")

            for action, edges in actual_state.edges_by_action.items():
                # print(action, edges)
                if states_dict[route[-1]] in edges:
                    action_selected = action
                    possible_states = possible_states.union(edges)
                    break
            if isinstance(device, TestingDevice):
                print(f"Trying to go to {route[-1]}, making {action_selected}")

        if action_selected is not None:
            await action_selected.act(device)
        else:
            possible_states.add(actual_state)
        
        checked_states:set[State] = set()

        retries = 25
        while len(checked_states) != 1 and retries != 0:
            checked_states:set[State] = set()
            if not isinstance(device, TestingDevice):
                screencap = np.array(Image.open(await device.get_image()).convert("RGBA"))
            print(possible_states)
            for state in possible_states:
                if isinstance(device, TestingDevice):
                    response = await asyncio.to_thread(input, f"Should be in the state ({state.alias})? ")
                    while response.lower() not in {"si", "s", "no", "n", "yes", "y"}:
                        response = await asyncio.to_thread(input, f"Should be in the state ({state.alias})? ")
                    if response.lower() not in {"no", "n"}:
                        checked_states.add(state)
                    # print(checked_states)
                elif state.can_be_in_this_state(screencap):
                    checked_states.add(state)
            retries -= 1
        if retries == 0:
            raise ValueError("I don't know where I am")
        
        new_state = checked_states.pop()
        if (actual_state.alias, new_state.alias) not in edges_traveled:
            edges_traveled[(actual_state.alias, new_state.alias)] = 0
        edges_traveled[(actual_state.alias, new_state.alias)] += 1
        
        actual_state = new_state
        print(edges_traveled)
        




        
        # check state

        # actual_node = "None"
        
         
    # Primero calculo una ruta a target y la intento seguir, los tap que tengan un weigth de 1s y los none de 5s
    # Si estoy en la ruta la sigo, si la termino o me pierdo, recalculo
    # en cada paso, si se sobrepasa algún limite se sale del bucle

    # Si está en un camino y una acción una acción lleva a cumplir un límite, evita esa acción, a no ser que sea el target

    # Por ejemplo, si está limitado a hacer un especial (cuando haya más disponibles), pues ese trade de debería aceptarlo, pero tampoco haría falta que se bloquease, con que espere a que el otro lo cambie sería suficiente

if __name__ == "__main__":
    graph = load_graph("DeviceTemplate/trade_graph.json")
    # print(graph)
    route = calculate_shortest_path(graph, "profile_selected", "trade_received")
    print(route)
    trade_2 = asyncio.run(complete_task(TestingDevice(), graph, ("trade_received", "profile_selected"), {("trade_received", "profile_selected"): 2}))