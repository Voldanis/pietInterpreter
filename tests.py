import unittest
from piet import PietInterpreter, ProgramState, DirPointerState, CodelCounterState
from normalizer import Normalizer, Pixel
import numpy as np
import os
from PIL import Image

class TestPietFib(unittest.TestCase):
    def setUp(self):
        self.interp = PietInterpreter.__new__(PietInterpreter)
        self.interp.stack = []
        self.interp.state = ProgramState()

    def test_real_fib_cycle(self):
        self.interp.stack = [1, 1]
        
        self.interp._execute_cmd("duplicate", 0)
        self.assertEqual(self.interp.stack, [1, 1, 1])
        
        self.interp.stack.append(3) 
        self.interp.stack.append(1) 
        self.interp._execute_cmd("roll", 0)
        
        self.interp._execute_cmd("add", 0)
        self.assertEqual(self.interp.stack, [1, 2])

    def test_fib_math_progression(self):
        self.interp.stack = [1, 2]
        
        self.interp._execute_cmd("duplicate", 0) 
        self.interp.stack.append(3) 
        self.interp.stack.append(1) 
        self.interp._execute_cmd("roll", 0)      
        self.interp._execute_cmd("add", 0)       
        
        self.assertEqual(self.interp.stack, [2, 3])
        
        self.interp._execute_cmd("duplicate", 0) 
        self.interp.stack.append(3) 
        self.interp.stack.append(1) 
        self.interp._execute_cmd("roll", 0)      
        self.interp._execute_cmd("add", 0)       
        
        self.assertEqual(self.interp.stack, [3, 5])


class TestNormalizerColor(unittest.TestCase):
    def test_normalize_black(self):
        # Все, что меньше 63, должно стать 0
        self.assertEqual(Normalizer.try_normalize_color(0), (0, True))
        self.assertEqual(Normalizer.try_normalize_color(62), (0, True))

    def test_normalize_shade(self):
        # Чекаем границы вокруг 192:
        self.assertEqual(Normalizer.try_normalize_color(192), (192, True))
        self.assertEqual(Normalizer.try_normalize_color(168), (192, True))
        self.assertEqual(Normalizer.try_normalize_color(216), (192, True))

    def test_normalize_white(self):
        # Все, что >= 255-24
        self.assertEqual(Normalizer.try_normalize_color(255), (255, True))
        self.assertEqual(Normalizer.try_normalize_color(231), (255, True))

    def test_unsupported_colors(self):
        # Цвета, которые не попадают в диапазоны
        # 100 (между черным 63 и серым 168)
        val, success = Normalizer.try_normalize_color(100)
        self.assertFalse(success)
        self.assertEqual(val, 100)
        
        # 220 (между серым 216 и белым 231)
        val, success = Normalizer.try_normalize_color(220)
        self.assertFalse(success)
        self.assertEqual(val, 220)


class TestNormalizerPixel(unittest.TestCase):
    def setUp(self):
        self.Pixel = Pixel

    def test_pixel_full_normalization(self):
        # Жоск чистый красный (255, 0, 0)
        p = self.Pixel([255, 0, 0])
        norm_p = Normalizer.try_normalize_pixel(p)
        self.assertEqual((norm_p.r, norm_p.g, norm_p.b), (255, 0, 0))

        # Уже не жоск чистый розовый (типа измениться должен)
        p_noisy = self.Pixel([240, 180, 200])
        norm_p_noisy = Normalizer.try_normalize_pixel(p_noisy)
        self.assertEqual((norm_p_noisy.r, norm_p_noisy.g, norm_p_noisy.b), (255, 192, 192))

    def test_pixel_partial_failure(self):
        # не попадает в границы нормализации
        # Надеюсь, что должно вернуть исходный пиксель без изменений
        p_broken = self.Pixel([255, 100, 0])
        norm_p = Normalizer.try_normalize_pixel(p_broken)

        self.assertEqual((norm_p.r, norm_p.g, norm_p.b), (255, 100, 0))
        # Проверяем, что ниче не изменилось
        self.assertEqual(norm_p.g, 100) 

    def test_pixel_black_and_white(self):
        # Граничный случай для черного
        p_black = self.Pixel([60, 10, 5])
        norm_p = Normalizer.try_normalize_pixel(p_black)
        self.assertEqual((norm_p.r, norm_p.g, norm_p.b), (0, 0, 0))

        # Ну и граничный случай для белого
        p_white = self.Pixel([235, 240, 250])
        norm_p = Normalizer.try_normalize_pixel(p_white)
        self.assertEqual((norm_p.r, norm_p.g, norm_p.b), (255, 255, 255))


class TestNormalizerImageArray(unittest.TestCase):
    def setUp(self):
        self.Pixel = Pixel

    def test_normalize_matrix(self):
        # Крч матрица задана так:
        # (0,0) - почти красный, (0,1) - грязный цвет
        # (1,0) - почти белый, (1,1) - чистый черный
        matrix = [
            [self.Pixel([250, 5, 5]),   self.Pixel([100, 100, 100])],
            [self.Pixel([240, 240, 240]), self.Pixel([0, 0, 0])]
        ]
        
        normalized = Normalizer.normalize_pixels(matrix)
        
        # Чекаем размеры
        self.assertEqual(len(normalized), 2)
        self.assertEqual(len(normalized[0]), 2)
        
        # Чекаем нормализацию красного
        self.assertEqual((normalized[0][0].r, normalized[0][0].g, normalized[0][0].b), (255, 0, 0))
        
        # Чекаем, что грязный цвет (100) остался без изменений
        self.assertEqual(normalized[0][1].r, 100)
        
        # Чекаем нормализацию белого
        self.assertEqual((normalized[1][0].r, normalized[1][0].g, normalized[1][0].b), (255, 255, 255))

    def test_empty_matrix(self):
        # Чек на пустой вход
        self.assertEqual(Normalizer.normalize_pixels([]), [])


class TestCodelSizeDiscovery(unittest.TestCase):
    def test_find_max_codel_size_simple(self):
        # Типа изображение 4на4, где кодел = 2
        # Каждые 2на2 пикселя одного цвета
        data = np.zeros((4, 4, 3), dtype=int)
        data[0:2, 0:2] = [255, 0, 0] # Красный блок
        data[0:2, 2:4] = [0, 255, 0] # Зеленый блок
        data[2:4, 0:2] = [0, 0, 255] # Синий блок
        data[2:4, 2:4] = [0, 0, 0]   # Черный блок
        
        size = Normalizer.find_max_codel_size(data)
        self.assertEqual(size, 2)

    def test_find_max_codel_size_one(self):
        # Если пиксели перемешаны, размер кодела должен быть 1
        data = np.zeros((2, 2, 3), dtype=int)
        data[0, 0] = [255, 0, 0]
        data[0, 1] = [0, 255, 0]
        data[1, 0] = [0, 0, 255]
        data[1, 1] = [255, 255, 255]
        
        size = Normalizer.find_max_codel_size(data)
        self.assertEqual(size, 1)


class TestNormalizerScaling(unittest.TestCase):
    def setUp(self):
        from normalizer import Pixel
        self.Pixel = Pixel

    def test_scale_image_logic(self):
        """Проверяем, что изображение 4x4 при коделе 2 превращается в 2x2."""
        # Делаем массив 4x4x3
        data = np.zeros((4, 4, 3), dtype=np.uint8)
        data[0:2, 0:2] = [255, 0, 0]   # Красный
        data[0:2, 2:4] = [0, 255, 0]   # Зеленый
        data[2:4, 0:2] = [0, 0, 255]   # Синий
        data[2:4, 2:4] = [255, 255, 0] # Желтый

        scaled = Normalizer.scale_image(data, 2)

        # должно стать 2на2 пикселя
        self.assertEqual(scaled.shape[0], 2)
        self.assertEqual(scaled.shape[1], 2)
        
        # Проверяем цвета (щас обращаемся по индексам массива)
        # [0, 0] — левый верхний кодел
        np.testing.assert_array_equal(scaled[0, 0], [255, 0, 0])
        # [1, 1] — правый нижний кодел
        np.testing.assert_array_equal(scaled[1, 1], [255, 255, 0])


class TestNormalizerFinal(unittest.TestCase):
    def test_normalize_integration_real_file(self):
        test_img = r"C:\Users\user\Documents\GitHub\pietInterpreter\ДляТестов.png"
        
        if not os.path.exists(test_img):
            self.skipTest(f"Файл {test_img} не найден, проверь путь!")

        result = Normalizer.normalize(test_img, 0)

        # Проверяем структуру объекта
        self.assertTrue(hasattr(result, 'pixels'), "Объект должен содержать поле pixels")
        self.assertTrue(hasattr(result, 'width'), "Объект должен содержать поле width")
        self.assertTrue(hasattr(result, 'height'), "Объект должен содержать поле height")

        # Проверяем типы данных
        self.assertIsInstance(result.pixels, list, "Поле pixels должно быть списком")
        
        if result.width > 0 and result.height > 0:
            top_left_pixel = result.pixels[0][0]
            
            # Проверяем, что это объект Pixel и он нормализован
            print(f"\n[LOG] Цвет первого кодела: ({top_left_pixel.r}, {top_left_pixel.g}, {top_left_pixel.b})")

        else:
            self.fail("Нормализатор вернул пустое изображение")


class TestNormalizerEdgeCases(unittest.TestCase):
    def test_get_primes_limit(self):
        """Проверка защиты от слишком больших чисел."""
        with self.assertRaises(ValueError):
            Normalizer.get_primes(2001)

    def test_scale_image_with_objects(self):
        """Проверка, что масштаб сохраняет объекты Pixel."""
        from normalizer import Pixel
        p1 = Pixel([255, 0, 0])
        p2 = Pixel([0, 255, 0])
        matrix = [[p1, p1], [p1, p1]] 
        
        # очень жду и надеюсь, что после сжатия останется 1на1 и тот же объект
        scaled = Normalizer.scale_image(matrix, 2)
        self.assertEqual(scaled.shape, (1, 1))
        self.assertIs(scaled[0, 0], p1)

    def test_find_max_codel_size_prime_gcd(self):
        """Если НОД — простое число, должен найти его."""
        # Картинка 7x7 одного цвета. GCD = 7. 
        # Если 7 есть в primes.txt, должен вернуть 7.
        data = np.zeros((7, 7, 3), dtype=np.uint8)
        size = Normalizer.find_max_codel_size([[Pixel([0,0,0]) for _ in range(7)] for _ in range(7)])
        self.assertEqual(size, 7)


class TestProgramState(unittest.TestCase):
    def setUp(self):
        self.state = ProgramState()

    def test_pointer_rotation(self):
        """Проверка поворота указателя направления (DP)."""
        self.state.pointer(1) # Поворот на 90 градусов по часовой
        self.assertEqual(self.state.dp, DirPointerState.DOWN)
        self.state.pointer(2) # Поворот на 180
        self.assertEqual(self.state.dp, DirPointerState.UP)
        self.state.pointer(1) # Возврат в исходное
        self.assertEqual(self.state.dp, DirPointerState.RIGHT)

    def test_switch(self):
        """Проверка переключения счетчика коделов (CC)."""
        initial_cc = self.state.cc
        self.state.switch(1)
        self.assertNotEqual(self.state.cc, initial_cc)
        self.state.switch(2) # Четное число переключений возвращает состояние
        self.assertNotEqual(self.state.cc, initial_cc)


class TestInterpreterCommands(unittest.TestCase):
    def setUp(self):
        # Используем __new__ чтобы не грузить реальную картинку в тестах логики
        self.interp = PietInterpreter.__new__(PietInterpreter)
        self.interp.stack = []
        self.interp.state = ProgramState()

    def test_arithmetic(self):
        """Проверка add, subtract, multiply, divide, mod."""
        self.interp.stack = [10, 3]
        self.interp._execute_cmd("add", 0)
        self.assertEqual(self.interp.stack, [13])

        self.interp.stack = [10, 3]
        self.interp._execute_cmd("subtract", 0) # 10 - 3
        self.assertEqual(self.interp.stack, [7])

        self.interp.stack = [10, 3]
        self.interp._execute_cmd("divide", 0) # 10 // 3
        self.assertEqual(self.interp.stack, [3])

    def test_roll(self):
        """Проверка сложной команды roll."""
        # Стек: [4, 3, 2, 1], глубина 3, количество 1
        self.interp.stack = [4, 3, 2, 1, 3, 1]
        self.interp._execute_cmd("roll", 0)
        # Ожидаем, что верхние 3 элемента [3, 2, 1] сдвинутся: [1, 3, 2]
        self.assertEqual(self.interp.stack, [4, 1, 3, 2])

    def test_not_and_greater(self):
        """Проверка логических команд."""
        self.interp.stack = [5]
        self.interp._execute_cmd("not", 0)
        self.assertEqual(self.interp.stack, [0]) # Not 5 = 0

        self.interp.stack = [0]
        self.interp._execute_cmd("not", 0)
        self.assertEqual(self.interp.stack, [1]) # Not 0 = 1

        self.interp.stack = [5, 10]
        self.interp._execute_cmd("greater", 0) # 5 > 10?
        self.assertEqual(self.interp.stack, [0])
        
        
if __name__ == '__main__':
    unittest.main()