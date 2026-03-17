from objects import *

# load all states as prestates and save in a dict, then resolve references

states: dict[str,
    tuple[
        list[str],
        list[tuple[TypeAction, tuple[str|int, ...], str]],
        list[str]]]

states = {}


resolution = (1000, 1000)

# id: masks, actions -> id, spontaneous[id]
states["profile_selected"] = ["mask.png"], [(TypeAction.TAP, (200, 200), "trade")], []

pre_states: dict[str, PreState]
pre_states = {}
for k, v in states.items():
    actions = {Action(a[0], *a[1]): a[2] for a in v[1]}
    pre_states[k] = PreState(v[0], actions, v[2], resolution)

# no se pueden resolver las referencias sin tener dentro de una clase ambas opciones como válidas
# porque aunque haga prestate, no estan definidos todos los states cuando vaya a empezar a definirlos
# y si me guardo las referencias y edito las referencias?, como lo que hago en filtered_iv_search