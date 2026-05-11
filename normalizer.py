import math
from enum import Enum
from PIL import Image  # сделать установку в коде
import numpy as np


class ColorsSimple(Enum):
    LIGHT_PINK = (255, 192, 192)
    LIGHT_YELLOW = (255, 255, 192)
    LIGHT_GREEN = (192, 255, 192)
    LIGHT_CYAN = (192, 255, 255)
    LIGHT_BLUE = (192, 192, 255)
    LIGHT_PURPLE = (255, 192, 255)
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    GREEN = (0, 255, 0)
    CYAN = (0, 255, 255)
    BLUE = (0, 0, 255)
    PURPLE = (255, 0, 255)
    DARK_RED = (192, 0, 0)
    DARK_YELLOW = (192, 192, 0)
    DARK_GREEN = (0, 192, 0)
    DARK_CYAN = (0, 192, 192)
    DARK_BLUE = (0, 0, 192)
    DARK_PURPLE = (192, 0, 192)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)


class Pixel:
    def __init__(self, colors):
        self.r = colors[0]
        self.g = colors[1]
        self.b = colors[2]

    def __str__(self):
        return f"({self.r}, {self.g}, {self.b})"


class Normalizer:
    @staticmethod
    def normalize(image, in_scale_size):
        pixels = np.array(
            Normalizer.convet_image_to_pixels(
            Normalizer.normalize_pixels(image)))
        scale_size = in_scale_size if in_scale_size > 0 else Normalizer.find_max_codel_size(pixels)
        normalized_pixels = Normalizer.scale_image(pixels, scale_size)
        return NormalizedImage(normalized_pixels)

    @staticmethod
    def convet_image_to_pixels(image):
        """
        Конвертирует изображение в массив строк. Каждая строка - массив пикселей.
        """
        with Image.open(image) as img:
            img.load()
            rgb_img = img.convert("RGB")
            pixel_array = np.array(rgb_img)
            return [[Pixel(rgb) for rgb in line] for line in pixel_array]

    @staticmethod
    def try_normalize_color(color):
        black = 0
        shade = 192
        white = 255
        black_border = 63
        border_radius = 24

        if color < black_border:
            return black, True
        if shade - border_radius <= color <= shade + border_radius:
            return shade, True
        if white - border_radius <= color:
            return white, True
        return color, False

    @staticmethod
    def try_normalize_pixel(pixel):
        new_r, r_try = Normalizer.try_normalize_color(pixel.r)
        new_g, g_try = Normalizer.try_normalize_color(pixel.g)
        new_b, b_try = Normalizer.try_normalize_color(pixel.b)
        if r_try and g_try and b_try:
            return Pixel([new_r, new_g, new_b])
        return pixel

    @staticmethod
    def normalize_pixels(pixels):
        norm_pixels = []
        for line in pixels:
            norm_pixels.append([])
            for pixel in line:
                norm_pixels[-1].append(Normalizer.try_normalize_pixel(pixel))
        return norm_pixels

    @staticmethod
    def get_primes(n):
        if n > 2000:
            raise ValueError("n должно быть не больше 2000")

        with open('primes.txt', 'r') as f:
            first_line = f.readline().strip()
            primes = list(map(int, first_line.split()))
            if n >= 500:
                second_line = f.readline().strip()
                primes.extend(map(int, second_line.split()))
        return [p for p in primes if p <= n]

    @staticmethod
    def check_squares(pixes, square_size):
        height, width = pixes.shape[:2]
        h_blocks = height // square_size
        w_blocks = width // square_size
        reshaped = pixes.reshape(h_blocks, square_size, w_blocks, square_size, -1)

        for i in range(h_blocks):
            for j in range(w_blocks):
                block = reshaped[i, :, j, :, :]
                if not np.all(block == block[0, 0]):
                    return False
        return True

    @staticmethod
    def find_max_codel_size(pixels):
        height, width = pixels.shape[:2]
        gsd = math.gcd(height, width)
        primes = Normalizer.get_primes(gsd)[::-1]

        for size in primes:
            if height % size == 0 and width % size == 0:
                if Normalizer.check_squares(pixels, size):
                    return size
        return 1

    @staticmethod
    def scale_image(pixels, scale_size):
        result = []
        height, width = pixels.shape[:2]
        for i in range(0, scale_size, height):
            row = []
            for j in range(0, scale_size, width):
                    row.append(pixels[i][j])
            result.append(row)
        return result


class NormalizedImage:
    def __init__(self, pixels):
        self.pixels = pixels
        self.height, self.width = pixels.shape[:2]
