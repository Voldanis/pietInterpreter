from PIL import Image
import numpy as np
import os


def check_colors(image_path):
    """
    Оптимизированная версия с использованием векторизации NumPy.
    """
    allowed_colors_set = {
        (255, 192, 192), (255, 255, 192), (192, 255, 192), (192, 255, 255),
        (192, 192, 255), (255, 192, 255), (255, 0, 0), (255, 255, 0),
        (0, 255, 0), (0, 255, 255), (0, 0, 255), (255, 0, 255),
        (192, 0, 0), (192, 192, 0), (0, 192, 0), (0, 192, 192),
        (0, 0, 192), (192, 0, 192), (255, 255, 255), (0, 0, 0)
    }

    # Преобразуем множество в массив NumPy для быстрых операций
    allowed_colors_array = np.array(list(allowed_colors_set))

    # Загружаем изображение
    with Image.open(image_path) as img:
        img.load()
        rgb_img = img.convert("RGB")
        pixel_array = np.array(rgb_img)

    # Изменяем форму для удобной проверки
    original_shape = pixel_array.shape
    pixels_flat = pixel_array.reshape(-1, 3)

    # Создаем массив для отметки допустимых цветов
    is_allowed = np.zeros(len(pixels_flat), dtype=bool)

    # Проверяем каждый цвет из списка допустимых
    for allowed_color in allowed_colors_array:
        # Сравниваем все пиксели с текущим допустимым цветом
        matches = np.all(pixels_flat == allowed_color, axis=1)
        is_allowed = np.logical_or(is_allowed, matches)

    # Находим недопустимые пиксели
    invalid_mask = ~is_allowed
    if np.any(invalid_mask):
        invalid_pixels = pixels_flat[invalid_mask]
        invalid_colors = set(map(tuple, invalid_pixels))
        return False, list(invalid_colors)

    return True, []


def get_all_filenames(folder_path):
    filenames = []

    # Перебираем все элементы в папке
    for item in os.listdir(folder_path):
        # Формируем полный путь к элементу
        item_path = os.path.join(folder_path, item)

        # Проверяем, что это файл (не папка)
        if os.path.isfile(item_path):
            filenames.append(item_path)

    return filenames

