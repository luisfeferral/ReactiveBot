## ReactiveBot

ReactiveBot is a small, modular framework to build screen-based automation driven by a graph of states, masks and actions. The repository provides a core implementation (the base types and graph machinery) plus optional adapters and helper modules that use ADB (Android Debug Bridge) to interact with a device. The project is intentionally modular so new adapters or convenience layers can be added without changing the core.

This README explains the repository structure, how the parts relate, a quick way to run the included example, and a short list of ideas for future improvements.

## Project overview

- Core concept: represent an app/workflow as a graph of states where each state is recognized using one or more mask images or filters. Actions move the automation from one state to the next.
- `objects.py` contains the base implementation: the data structures and logic for graphs, states, masks and actions. Treat this file as the core library.
- `adb_controller.py` implements an adapter that uses ADB to communicate with an Android device (take screenshots, perform taps/swipes, push files, etc.).
- `adb_actions.py` builds on top of `adb_controller.py` and exposes higher-level convenience functions that are easier to use in automation scripts.
- `pokemon_go_example.py` is a concrete example of how the project can be used to automate a real scenario (kept as an example and starting point, the masks are for an specific device probably you must redo all the masks before you can test on your device).

## Repository structure (important files)

- `objects.py` — Core classes and functions (graph, state, mask, action). The heart of the project.
- `adb_controller.py` — ADB device adapter. Provides primitives to interact with an Android device (screenshot, input events).
- `adb_actions.py` — Convenience layer with common actions built using the ADB adapter.
- `pokemon_go_example.py` — Example script showing how the pieces can be tied together for a particular use case.
- `DeviceTemplate/` — Example device templates and sample graph JSON files used by examples.
- `requirements.txt` and `pyproject.toml` — Python dependency manifests.

## Quick start (Windows / cmd.exe)

1. Create and activate a virtual environment (recommended):

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

2. Install dependencies:

```cmd
pip install -r requirements.txt
```

The example is intentionally a starting point — inspect `pokemon_go_example.py` to see how the core (`objects.py`) and the ADB adapter (`adbcontroller.py` / `adb_actions.py`) are used together.

## How to use the project

- Develop or author a graph that models the states and transitions of your target app or workflow. The `DeviceTemplate/` directory contains sample JSON graphs you can inspect.
- Implement or adapt masks (images) that let the core state recognition identify each state.
- Use the classes in `objects.py` to load/build a graph and run the automation loop. For ADB device interaction, you can use `adb_controller.py`.
- If you want a quicker API for common tasks, use `adb_actions.py` which adds convenience functions on top of the ADB primitives.

Note: The exact public API (class and method names) lives in `objects.py`. For a complete, working example of API usage, open `pokemon_go_example.py`.

## Future ideas and possible improvements

- That the initial state will be a list of possible states instead that can be only one. This will help to start the task completion in a position without a previous manual prep.
- That the states could have variants, this will be like other states but inside the same, so you can refer to the different variants with only a state name. They will be different of add several masks to the same state because there will be designed for have different actions, not different edges, like when two states only differs in position of the buttons but have the same options.
- The mask image name could be a regex pattern and this will help to write the json file a bunch.
- The actual recognizing system is a bit limited when you want to diferenciate a certain text from any other text, because all the coincident parts will be in both but the system wants that a state is recognized if matches one and only one state. Probably the solution will be have negative masks.
- Have an editor for the json graphs, something that could help visualizating neighbour states, actions over captions or even a live image of a device and that will help in the writing of state aliases and mask file names (or even a selection tool from a list).
- The graph will have arguments that are applied when the graph is building. This will help when a graph will have and action that can be slighty different like different text to introduce.

## Notes

- The repository focuses on a small, clear core (`objects.py`) and optional layers/adapters for specific environments (ADB in this repo). This separation makes it easy to add other adapters later.
- For detailed API and examples, inspect `objects.py`, `adb_controller.py`, `adb_actions.py` and `pokemon_go_example.py`.