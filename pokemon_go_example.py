from adb_actions import *
from adb_controller import select_and_load_device

if __name__ == "__main__":
    graph = load_graph("DeviceTemplate/pokemon_go_trade_v2/trade_graph.json")

    print("Please, select the device that you wanna to connect:")
    device = asyncio.run(select_and_load_device())
    
    print("Please go to the profile of the friend what yo wanna to trade")
    asyncio.run(complete_task(device=device, states_dict=graph, target=("trade_received", "friend_selected"),
                              limits_loop={("trade_received", "friend_selected"): int(input("How many pokemon de you wanna to trade? ")),
                                           ("selecting_specific_tag_for_trade", "favorite"): 1,
                                           ("trade_received", "lucky_friend_selected"): 1,
                                           ("trade_limit_reached", "friend_selected"): 1},
                              training_wheels_protocol=True))
    
