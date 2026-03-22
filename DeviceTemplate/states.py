from objects import *

states: dict[str,
            tuple[list[str],
                    dict[Optional[Action], list[str]]]]

states = {}

# resolution = (1000, 1000)

# the first defined state will be the initial state of the circuit
# id: masks, actions -> id
states["profile_selected"] = ["mask.png"], {TapEllipseAction(Ellipse(540, 1870, 130, 80)): ["waiting_trade"]}
states["waiting_trade"] = ["mask.png"], {None: ["trade_selection", "trade_expired"]}
states["trade_selection"] = ["mask.png"], {TapEllipseAction(Ellipse(191, 706, 75, 94)): ["first_confirm_trade"], None: ["trade_expired"]}
states["first_confirm_trade"] = ["mask.png"], {TapEllipseAction(Ellipse(540, 1906, 300, 70)): ["last_confirm_trade"], None: ["trade_expired"]}
states["last_confirm_trade"] = ["mask.png"], {TapEllipseAction(Ellipse(200, 1174, 200, 74)): ["waiting_confirm"], None: ["trade_expired"]}
states["waiting_confirm"] = ["mask.png"], {None: ["trade_received", "trade_expired"]}
states["trade_received"] = ["mask.png"], {TapEllipseAction(Ellipse(540, 2131, 50, 50)): ["profile_selected"]}
states["trade_expired"] = ["mask.png"], {TapEllipseAction(Ellipse(540, 2131, 50, 50)): ["profile_selected"]} # bad coordinates

# si no se puede hacer import desde una carpeta superior, lo suyo será hacer un editor que me permita hacer esto de manera fácil y luego tenerlo en un formato del estilo de json o similar y que se importe desde ahí
# el editor podría tener integrado para ver un dispositivo en tiempo real, sería los ideal una parte en la izquierda en la que se vea la pantalla o una recreación y las acciones sobre ella, si clickas en una que se mande que y que se mueva al estado que toque
# una parte central con las mascaras y sería ideal que permitiera crearlas fácilmente con las capturas de la izquierda y seleccionando rectangulos y borrando (obviamente lo ideal es una herramienta de seleccion mágica pporque normalmente queremos pillar los botones y no son reactangulos)
# y en la izquierda que se pueda ver el grafo, desde ahi tambien se tendría que poder hacer acciones en el dispositivo, aunque para eso ya habría que traerse el algoritmo de ruta para poder hacer varios cambios de state

# obviamente aprovechar para mirar que el grafo es válido que los nombres no se pisan...

# lo que menos me gusta del editor es que va a estar muy acoplado al código pero va a ir a aparte estonces se puede como quedar atrás, pero como de momento no lo voy a implementar que unos grafos sencillos los puedo hacer a mano