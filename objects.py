from __future__ import annotations

import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod
import asyncio
import numpy as np
from typing import IO, Optional
import json
import pathlib
import time
from PIL import Image
from random import random as _random
from math import sin as _sin, cos as _cos, pi as _pi, sqrt as _sqrt

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class Mask:
    _rgb_array: np.ndarray # rgb from the png file
    _filtered_array: np.ndarray # bool array with the points that will be used for comparison
    _dimensions: tuple[int, int] # shape of the png file, first condition to check for a match
    def __init__(self, img_source) -> None:
        img = np.array(Image.open(img_source).convert("RGBA"))
        self._rgb_array = img[:, :, :3]
        self._dimensions = self._rgb_array.shape[:2]
        self._filtered_array = img[:, :, 3] >= 128 # / 255
    def mask_match(self, img: np.ndarray, threshold=.97) -> bool:
        img_rgb = img[:, :, :3]
        if self._dimensions != img_rgb.shape[:2]:
            logger.debug(f"{self._dimensions} != {img_rgb.shape[:2]}")
            return False
        percentage = np.mean((self._rgb_array[self._filtered_array] == img_rgb[self._filtered_array]).all(axis=1))
        logger.debug(f"mask matching: {percentage:.2%}")
        if logger.isEnabledFor(logging.DEBUG) and percentage >= threshold and percentage < 1:
            self.get_diff_image(img)
        return percentage >= threshold
        # same as threshold 1, not very recommended, sometimes some pixels slighty change
        return bool(np.all(self._rgb_array[self._filtered_array] == img_rgb[self._filtered_array]))
    def get_diff_image(self, img: np.ndarray, output_name="debug.png"):
        img_rgb = img[:, :, :3]
        matches = (img_rgb == self._rgb_array).all(axis=2)
        errors = (~matches) & self._filtered_array

        debug_img = img.copy()

        # Paint errors in red
        debug_img[errors] = [255, 0, 0, 255]

        Image.fromarray(debug_img).save(output_name)


@dataclass
class Ellipse:
    center_x: int
    center_y: int
    radius_x: int
    radius_y: int

    def get_random_point(self) -> tuple[int, int]:
        # We will calculate a random point on a unit circle and then transfer it to the ellipse
        # We take a random angle
        theta = _random() * 2 * _pi

        # The square root compensates for the difference in area near the center and at the edges
        r = _sqrt(_random())

        # Point on unit circle
        u = r * _cos(theta)
        v = r * _sin(theta)

        # Scaling to the ellipse
        x = self.center_x + u * self.radius_x
        y = self.center_y + v * self.radius_y

        return int(x), int(y)
    
    def __str__(self) -> str:
        return f"x: {self.center_x} ± {self.radius_x}; y: {self.center_y} ± {self.radius_y}"


class CapturableDevice(ABC):
    @abstractmethod
    async def get_image(self) -> IO[bytes]: ...


class Action[DeviceType:CapturableDevice](ABC):
    registry = {}

    @classmethod
    def register(cls, action_type: str):
        def decorator(subclass):
            cls.registry[action_type] = subclass
            return subclass
        return decorator

    @classmethod
    def from_dict(cls, data) -> Action[DeviceType]:
        action_type:str = data["type"]
        subclass = cls.registry[action_type]
        return subclass[DeviceType].from_dict(data)
    
    @abstractmethod
    def __str__(self) -> str: ...

    def __repr__(self) -> str:
        return self.__str__()

    @abstractmethod
    async def act(self, device: DeviceType) -> None: ...

    @abstractmethod
    def get_weight(self) -> float: ...

    def get_actions(self) -> list[Action]: 
        return [self]

    def __add__(self, other: int | Action) -> MacroAction[DeviceType]:
        if isinstance(other, int):
            return self + WaitAction[DeviceType](other)
        elif isinstance(other, Action):
            return MacroAction[DeviceType](self.get_actions() + other.get_actions())
        raise NotImplemented
    # hashable
    def __hash__(self) -> int:
        return hash(self.__str__())
    def __eq__(self, other: Action) -> bool:
        if not isinstance(other, Action):
            return NotImplemented
        return str(self) == str(other)



@Action.register("macro")
class MacroAction[DeviceType:CapturableDevice](Action):
    actions: list[Action]
    def __init__(self, actions: list[Action]) -> None:
        self.actions = actions
    @classmethod
    def from_dict(cls, data):
        actions = data["actions"]
        return cls(
            list(Action.from_dict(a) for a in actions)
        )
    def get_weight(self) -> float:
        return sum(action.get_weight() for action in self.actions)
    def __str__(self):
        return f"[macro]: ({' + '.join(str(a) for a in self.actions)})"
    async def act(self, device: DeviceType) -> None:
        for a in self.actions:
            await a.act(device)
    def get_actions(self) -> list[Action]:
        return self.actions


@Action.register("wait")
class WaitAction[DeviceType:CapturableDevice](Action):
    time_ms: int
    time_s: float
    def __init__(self, time_ms: int) -> None:
        self.time_ms = time_ms
        self.time_s = time_ms / 1000
    @classmethod
    def from_dict(cls, data):
        return cls(time_ms=data["time_ms"])
    def get_weight(self) -> float:
        return self.time_s
    def __str__(self):
        return f"[wait] {self.time_ms} ms"
    async def act(self, _: DeviceType) -> None:
        await asyncio.sleep(self.time_s)


# # this is an example of a useful action but all the actions are built in the different specific modules where the devices are already defined
# SpecificAction = Action[SpecificDevice]


# @Action.register("tap")
# class TapAction[_](SpecificAction):
#     position: tuple[int, int]
#     weight: float
#     def __init__(self, position_x:int, position_y:int, weight:float=1) -> None:
#         self.position = position_x, position_y
#         self.weight = weight
#     @classmethod
#     def from_dict(cls, data):
#         pos = data["position"]
#         kwargs = {}
#         if "weight" in data:
#             kwargs["weight"] = data["weight"]

#         return cls(
#             pos["x"], pos["y"],
#             **kwargs
#         )
#     def get_weight(self) -> float:
#         return self.weight
#     def __str__(self):
#         return f"[tap] pos: {self.position}"
#     async def act(self, device: SpecificDevice) -> None:
#         await device.tap(*self.position)


class State[DeviceType:CapturableDevice]:
    alias: str
    # if there aren't masks, the state can be possible
    masks: Optional[list[Mask]]
    # the set[State] assigned to None is the set with the spontaneous states
    edges_by_action: dict[Optional[Action[DeviceType]], set[State[DeviceType]]]
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
            logging.debug(f"{self} is obvious state")
            return True
        logging.debug(f"checking: {self}")
        return any(m.mask_match(screen_img) for m in self.masks)
    def connect(self, action: Optional[Action], edges: set[State[DeviceType]]):
        self.edges_by_action[action] = edges


class TestingDevice(CapturableDevice):
    def __init__(self):
        print("Device for debugging, only prints in console")

    async def get_image(self) -> None:
        print("get_image from TestingDevice called")
        return None


def load_graph[DeviceType:CapturableDevice](json_path: str) -> dict[Optional[str], State]:
    '''load states from a json file'''
    # will be used for the relative paths of the masks
    path = pathlib.Path(json_path).parent
    with open(json_path, "r") as f:
        data = json.load(f)
    
    # states:
    # Dictionary representing system states
    # Key (str): Alias of the state. They have to be different, they are used for referencing.
    # Value (tuple[list[str], dict[Optional[Action], list[str]]]):
    #   1. list[str]
    #      - List of the relative path for the masks of the state.
    #   2. dict[Optional[Action], list[str]]
    #      - Dictionary of transitions from this state to others.
    #      Key (Optional[Action]):
    #         - Action that triggers the transition.
    #         - Can be None if the transition is automatic (no action required).
    #      Value (list[str]):
    #         - List of target states that can be reached with that action.
    states:dict[str,tuple[list[str],dict[Optional[Action[DeviceType]],list[str]]]] = {}

    for state_id, state_data in data["states"].items():
        masks:list[str] = state_data["masks"]
        transitions:dict[Optional[Action[DeviceType]],list[str]] = {}

        for t in state_data["transitions"]:
            if t["action"] is None:
                transitions[None] = t["next_states"]
            else:
                built_action:Action[DeviceType] = Action[DeviceType].from_dict(t["action"])
                transitions[built_action] = t["next_states"]

        states[state_id] = (masks, transitions)


    nodes:dict[Optional[str], State[DeviceType]] = {}
    # 1. Create the nodes
    for reference, (masks, _) in states.items():
        if len(masks) != len(set(masks)):
            logger.warning(f"The state {reference} has dupped masks")
        nodes[reference] = State[DeviceType](
            reference,
            [Mask(str(path/m)) for m in masks] if masks else None
        )

    # 2. Once all the nodes are built, connect them together
    for reference, (_, actions) in states.items():
        if len(actions) == 0:
            # Cul-de-sac
            logger.warning(f"The state {reference} has no actions assigned, it's a cul-de-sac")
            pass
        for action, edges in actions.items():
            set_edges = set(edges)
            if len(edges) != len(set_edges):
                logger.info(f"The state {reference} has dupped references in the action {action}, only one is considered")
                pass
            if len(set_edges) == 0:
                # Cul-de-sac
                logger.warning(f"The state {reference} has no references in the action {action}")
                pass
            set_nodes = set(nodes[e] for e in set_edges)
            # In each set only one state can be maskless, otherwise they will not be self-exclusive
            if sum(n.is_obvious_state() for n in set_nodes) > 1:
                raise SyntaxError("An action can't derive in several states unchecked by masks")
            nodes[reference].connect(action, set_nodes)

    # 3. Check that all the references exist
    # This step is checked implictly in the step 2, because they raise KeyError otherwise


    # 4. Check that the all the nodes can reach all the graph
    # Isolated nodes have no sense, and so are isolated cycles.
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
    '''Returns the shortest path to the target, it uses Dijkstra'''
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

class UnknownState(Exception):
    '''Exception raised when the actual state can be identified with the actual possibles'''
    pass



async def complete_task[DeviceType:CapturableDevice](*, device: DeviceType, states_dict:dict[Optional[str],State[DeviceType]], target: tuple[str, str], limits_loop: dict[tuple[str,str],int], training_wheels_protocol=False):
    '''target = "edge_name1" -> "edge_name2", 
    if the goal is to reach the target a limited number of times, the times can be restricted in the limits.
    Returns actual_state, last_state to be able to connect different graphs'''
    if training_wheels_protocol:
        from mask_builder import coroutine_main as mask_builder
        print("Training wheels protocol activated, when the robot doesn't know where it is, instead of raise an Exception, it will ask the user if want use that image as new mask and it will ask where it is and continues from there")
        logger.info("Training wheels protocol activated")
        mask_list = []
    
    # edges traveled history for the limit checking
    edges_traveled: dict[tuple[str,str], int] = {}

    weight_spontaneous_actions = 5

    def in_limits(edges_traveled: dict[tuple[str,str], int], limits: dict[tuple[str,str], int]):
        for k, v in edges_traveled.items():
            if k in limits:
                logger.debug(k, edges_traveled[k], limits[k])
                if v >= limits[k]:
                    return False
        return True
    
    route = []
    actual_state:State[DeviceType] = states_dict[None]
    if not actual_state.is_obvious_state() and not actual_state.can_be_in_this_state(np.array(Image.open(await device.get_image()).convert("RGBA"))):
        raise UnknownState("I'm not where I'm supposed to start")
    last_state:Optional[State[DeviceType]] = None
    while True:
        if not in_limits(edges_traveled, limits_loop):
            return actual_state, last_state
        if last_state != actual_state:

            action_selected = None
            possible_states: set[State[DeviceType]] = set()
            if actual_state.alias == target[0]:
                for action, edges in actual_state.edges_by_action.items():
                    if states_dict[target[1]] in edges:
                        action_selected = action
                        possible_states = possible_states.union(edges)
                        break
                if (possible_states) == 0:
                    logger.critical("There is no way to reach the target")
                    raise ValueError("There is no way to reach the target")
                logger.debug(f"Trying to go to {target[1]}, making {action_selected}")
            else:
                if len(route) > 1 and route[-1] == actual_state.alias:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"I have reached {route.pop()}, I will follow the previous calculated routed")
                    else:
                        route.pop()
                else:
                    route = calculate_shortest_path(states_dict, actual_state.alias, target[0], weight_spontaneous_actions)
                    logger.debug(f"Recalculated route. New route: {route}")
                if (actual_state.alias, route[-1]) in limits_loop and edges_traveled.get((actual_state.alias, route[-1]),0) + 1 >= limits_loop[(actual_state.alias, route[-1])]:
                    # If it reaches a way that is banned by limits, it does nothing
                    # If doing nothing can't reach another state, it breaks the loop
                    if None in actual_state.edges_by_action:
                        possible_states = possible_states.union(actual_state.edges_by_action[None])
                    else:
                        return actual_state, last_state
                else:
                    for action, edges in actual_state.edges_by_action.items():
                        if states_dict[route[-1]] in edges:
                            action_selected = action
                            possible_states = possible_states.union(edges)
                            break
                    if (possible_states) == 0:
                        logger.critical(f"There is no way to reach the next step {route[-1]}")
                        raise ValueError(f"There is no way to reach the next step {route[-1]}")
                    logger.debug(f"Trying to go to {route[-1]}, making {action_selected}")
        last_state = actual_state

        if action_selected is not None:
            logger.debug(f"I'm in {actual_state}")
            if not isinstance(device, TestingDevice):
                await action_selected.act(device)
        else:
            possible_states.add(actual_state)
        
        checked_states:set[State[DeviceType]] = set()

        retries = 100
        time.sleep(.15) # This pause it is relevant when the animations are a little bit slow, because the robot could think that it won't change state
        while len(checked_states) != 1 and retries != 0:
            try:
                checked_states = set()
                if not isinstance(device, TestingDevice):
                    screencap = np.array(Image.open(await device.get_image()).convert("RGBA"))
                logger.debug(f"Possible states: {possible_states}")
                for state in possible_states:
                    if isinstance(device, TestingDevice):
                        response = await asyncio.to_thread(input, f"Should be in the state ({state.alias})? ")
                        while response.lower() not in {"si", "s", "no", "n", "yes", "y"}:
                            response = await asyncio.to_thread(input, f"Should be in the state ({state.alias})? ")
                        if response.lower() not in {"no", "n"}:
                            checked_states.add(state)
                    elif state.can_be_in_this_state(screencap):
                        checked_states.add(state)
                retries -= 1
            except KeyboardInterrupt:
                retries = 0
                break
        if retries == 0:
            if training_wheels_protocol:
                mask_list = await mask_builder(mask_list, device)
                numered_list = {i: m for i, m in enumerate(possible_states)}
                while True:
                    try:
                        for i, m in numered_list.items():
                            print(f"{i}. {m}")
                        print("Ctrl+C to exit")
                        response = input("Where I should be? ")
                        option = int(response)
                        if option in numered_list.keys():
                            checked_states = {numered_list[option]}
                            break
                    except KeyError:
                        pass
                    except KeyboardInterrupt:
                        logger.critical(f"No response to what is the actual state")
                        raise UnknownState("I don't know where I am")
            else:
                logger.critical(f"I think I was at {actual_state}")
                raise UnknownState("I don't know where I am")
        
        new_state = checked_states.pop()
        edges_traveled[(actual_state.alias, new_state.alias)] = edges_traveled.get((actual_state.alias, new_state.alias), 0) + 1
        actual_state = new_state