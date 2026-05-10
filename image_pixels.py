from PIL import Image  # сделать установку в коде
import numpy as np

with Image.open('one_bright.png') as img:
    img.load()
    rgb_img = img.convert("RGB")
    pixel_array = np.array(rgb_img)
    print(rgb_img.mode)
