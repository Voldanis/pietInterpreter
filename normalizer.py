import math
from enum import Enum
from PIL import Image  # сделать установку в коде
import numpy as np


class Pixel:
    def __init__(self, colors):
        self._r = colors[0]
        self._g = colors[1]
        self._b = colors[2]

    @property
    def r(self):
        return self._r

    @property
    def g(self):
        return self._g

    @property
    def b(self):
        return self._b

    def __str__(self):
        return f"({self.r}, {self.g}, {self.b})"

    def __eq__(self, other):
        if not isinstance(other, Pixel):
            return False # возможно стоит сравнивать с массивами/кортежами
        return self.r == other.r and self.g == other.g and self.b == other.b

    def __hash__(self):
        return hash((self.r, self.g, self.b))


class Normalizer:
    @staticmethod
    def normalize(image, in_scale_size=-1):
        """
        Метод получает пиксели из изображения.
        Заменяет их на цвета из палитры piet, если они чуть ярче или темнее.
        Высчитывает максимальный размер пикселя для картинки.
        Масштабирует изображения, заменяя все пиксели в одном коделе на 1 пиксель.
        """
        pixels = Normalizer.normalize_pixels(
            Normalizer.convet_image_to_pixels(image))
        scale_size = in_scale_size if in_scale_size > 0 else Normalizer.find_max_codel_size(pixels)
        codels = pixels if scale_size == 1 else Normalizer.scale_image(pixels, scale_size)
        return NormalizedImage(codels)

    @staticmethod
    def convet_image_to_pixels(image):
        """
        Конвертирует изображение в массив строк. Каждая строка - массив пикселей.
        """
        # исправлено описание
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
        for row in pixels:
            norm_pixels.append([])
            for pixel in row:
                norm_pixels[-1].append(Normalizer.try_normalize_pixel(pixel))
        return norm_pixels

    @staticmethod
    def check_squares(pixels, square_size):
        """
        Разбивает массив пикселей на квадраты и проверяет, что в каждом квадрате все пиксели одинаковы.
        """
        height, width = len(pixels), len(pixels[0])
        np_pixels = np.array(pixels)
        h_blocks = height // square_size
        w_blocks = width // square_size
        reshaped = np_pixels.reshape(h_blocks, square_size, w_blocks, square_size, -1)

        for i in range(h_blocks):
            for j in range(w_blocks):
                block = reshaped[i, :, j, :, :]
                if not np.all(block == block[0, 0]):
                    return False
        return True

    @staticmethod
    def find_max_codel_size(pixels):
        height, width = len(pixels), len(pixels[0])
        gsd = math.gcd(height, width)

        for size in range(gsd, 1, -1):
            if height % size == 0 and width % size == 0:
                if Normalizer.check_squares(np.array(pixels), size):
                    return size
        return 1

    @staticmethod
    def scale_image(pixels, scale_size):
        result = []
        height, width = len(pixels), len(pixels[0])
        for i in range(0, height, scale_size):
            row = []
            for j in range(0, width, scale_size):
                row.append(pixels[i][j])
            result.append(row)
        return result


class NormalizedImage:
    def __init__(self, codels):
        self.codels = codels
        self.height, self.width = len(codels), len(codels[0])
