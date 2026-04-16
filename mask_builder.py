from adb_controller import ControllableDeviceAsync, select_and_load_device
import asyncio
import numpy as np
from PIL import Image
import os
import time
from typing import Coroutine, Optional
from random import randint

async def intersect_mask(img_file: str, device: ControllableDeviceAsync):
    '''Takes a mask and applies to the actual screen image and saves the new mask assuming the screen is in the same state'''
    if not os.path.exists(img_file):
        await device.save_image(img_file)
        return

    last_mask = np.array(Image.open(img_file).convert("RGBA"))
    new_img = np.array(Image.open(await device.get_image()).convert("RGBA"))

    last_rgb = last_mask[:, :, :3]
    new_rgb = new_img[:, :, :3]
    last_alpha = last_mask[:, :, 3]

    # Solo consideramos píxeles que ya eran válidos
    valid_last = last_alpha >= 128

    # Coincidencia RGB
    matches = (last_rgb == new_rgb).all(axis=2)

    # Nuevos píxeles válidos = los que ya eran válidos Y siguen coincidiendo
    new_valid = valid_last & matches

    # Crear nueva máscara
    updated_mask = last_mask.copy()

    # Donde ya no coincide → hacer transparente
    updated_mask[~new_valid, 3] = 0

    # (opcional) asegurar alpha sólido en válidos
    updated_mask[new_valid, 3] = 255

    Image.fromarray(updated_mask).save(img_file)

async def use_img_file_as_template(img_file: str, new_img_file: str, device: ControllableDeviceAsync):
    '''Make a new mask using a file as template and actual receipt'''
    img_template = np.array(Image.open(img_file).convert("RGBA"))
    new_img = np.array(Image.open(await device.get_image()).convert("RGBA"))

    last_alpha = img_template[:, :, 3]

    # Solo consideramos píxeles que ya eran válidos
    valid_last = last_alpha >= 128

    # Crear nueva máscara
    new_mask = new_img.copy()

    # Donde ya no coincide → hacer transparente
    new_mask[~valid_last, 3] = 0

    # (opcional) asegurar alpha sólido en válidos
    new_mask[valid_last, 3] = 255

    Image.fromarray(new_mask).save(new_img_file)

def select_mask_to_intersect(mask_list: list[str]):
    '''Prints a list of masks and wait the user returns an option to select'''
    while True:
        try:
            for i, m in enumerate(mask_list):
                print(f"{i+1}. {m}")
            if len(mask_list) < 9:
                print(f"0. To add new masks.")
            print("Ctrl+C to exit")
            response = input("Option? ")
            option = int(response)
            if 0 < option <= len(mask_list):
                return mask_list[option-1]
            elif option == 0 and len(mask_list) < 9:
                mask_list.append(input("New mask? "))
                return mask_list[-1]
        except ValueError:
            pass

def manual_build(device):
    '''Enters in a loop where the user can made new masks or intersect with the already inserted'''
    mask_list: list[str] = []
    mask_list.append(input("New mask? "))
    asyncio.run(intersect_mask(mask_list[0], device))
    while True:
        try:
            asyncio.run(intersect_mask(select_mask_to_intersect(mask_list), device))
        except KeyboardInterrupt:
            return

def auto_build(mask_name:str, steps:int, action:Optional[Coroutine], device:ControllableDeviceAsync):
    '''Auto intersect different receipts with an action made in between'''
    while steps > 0:
        try:
            asyncio.run(intersect_mask(mask_name, device))
            if action is not None:
                asyncio.run(action)
            time.sleep(.5)
            steps -= 1
        except KeyboardInterrupt:
            return

async def coroutine_main(mask_list:list[str], device):
    '''Like the manual build but it is improved for can be used interspersed in another code'''
    if len(mask_list) == 0:
        mask_list.append(input("New mask? "))
        await intersect_mask(mask_list[0], device)
    else:
        await intersect_mask(select_mask_to_intersect(mask_list), device)
    return mask_list

if __name__ == "__main__":
    device = asyncio.run(select_and_load_device())
    manual_build(device)
    # auto_build(input("New mask? "), int(input("Steps? ")), None, device)
    # auto_build(input("New mask? "), int(input("Steps? ")), device.send_swipe(randint(920,980), randint(1550,1650), randint(520,560), randint(1550,1650), randint(200,250)), device)
    # asyncio.run(intersect_mask("template.png", device))
    # asyncio.run(use_img_file_as_template("DeviceTemplate/pokemon_go_trade_v2/waiting_other_confirms.png", "waiting_other_confirms_discount.png", device))