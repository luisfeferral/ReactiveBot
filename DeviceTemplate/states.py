from objects import *

states: states_builder

states = {}

# resolution = (1000, 1000)

# the first defined state will be the initial state of the circuit
# id: masks, actions -> id, spontaneous[id]
states["profile_selected"] = ["mask.png"], {TapEllipseAction(Ellipse(540, 1870, 130, 80)): ["waiting_trade"]}
states["waiting_trade"] = ["mask.png"], {None: ["trade_selection", "trade_expired"]}
states["trade_selection"] = ["mask.png"], {TapEllipseAction(Ellipse(191, 706, 75, 94)): ["first_confirm_trade"], None: ["trade_expired"]}
states["first_confirm_trade"] = ["mask.png"], {TapEllipseAction(Ellipse(540, 1906, 300, 70)): ["last_confirm_trade"], None: ["trade_expired"]}
states["last_confirm_trade"] = ["mask.png"], {TapEllipseAction(Ellipse(200, 1174, 200, 74)): ["traded_recibed"], None: ["trade_expired"]}
states["traded_recibed"] = ["mask.png"], {TapEllipseAction(Ellipse(540, 2131, 50, 50)): ["profile_selected"]}
states["trade_expired"] = ["mask.png"], {TapEllipseAction(Ellipse(540, 2131, 50, 50)): ["profile_selected"]} # bad coordinates