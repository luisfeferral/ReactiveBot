from objects import *

# load all states as prestates and save in a dict, then resolve references

states: states_builder

states = {}

resolution = (1000, 1000)

# the first defined state will be the initial state of the circuit
# id: masks, actions -> id, spontaneous[id]
states["profile_selected"] = ["mask.png"], {TapEllipseAction(Ellipse(540, 1870, 130, 80)): ["waiting_trade"]}
states["waiting_trade"] = ["mask.png"], {None: ["trade_selection"]}
states["trade_selection"] = ["mask.png"], {TapEllipseAction(Ellipse(191, 706, 75, 94)): ["first_confirm_trade"]}
states["first_confirm_trade"] = ["mask.png"], {TapEllipseAction(Ellipse(540, 1906, 300, 70)): ["last_confirm_trade"]}
states["last_confirm_trade"] = ["mask.png"], {TapEllipseAction(Ellipse(200, 1174, 200, 74)): ["traded_recibed"]}
states["traded_recibed"] = ["mask.png"], {TapEllipseAction(Ellipse(540, 2131, 50, 50)): ["profile_selected"]}


# no se pueden resolver las referencias sin tener dentro de una clase ambas opciones como válidas
# porque aunque haga prestate, no estan definidos todos los states cuando vaya a empezar a definirlos
# y si me guardo las referencias y edito las referencias?, como lo que hago en filtered_iv_search