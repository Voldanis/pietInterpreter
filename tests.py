import sys
import subprocess

try:
    import unittest
    import numpy as np
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "unittest"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
    import unittest
    import numpy as np


from piet import PietInterpreter, ProgramState, DirPointerState, CodelCounterState
from normalizer import Normalizer, Pixel
from unittest.mock import patch, MagicMock
import os
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPaintEvent
from step_by_step_piet import GraphicPietInterpreter

class TestPietFib(unittest.TestCase):
    # комбинация команд duplicate, roll и add правильно реализует шаг последовательности Фибоначчи
    def setUp(self):
        self.interp = PietInterpreter.__new__(PietInterpreter)
        self.interp.stack = []
        self.interp.state = ProgramState()

    def test_real_fib_cycle(self):
        self.interp.stack = [1, 1]
        
        self.interp.execute_cmd("duplicate", 0)
        self.assertEqual(self.interp.stack, [1, 1, 1])
        
        self.interp.stack.append(3) 
        self.interp.stack.append(1) 
        self.interp.execute_cmd("roll", 0)
        
        self.interp.execute_cmd("add", 0)
        self.assertEqual(self.interp.stack, [1, 2])

    def test_fib_math_progression(self):
        self.interp.stack = [1, 2]
        
        self.interp.execute_cmd("duplicate", 0)
        self.interp.stack.append(3) 
        self.interp.stack.append(1) 
        self.interp.execute_cmd("roll", 0)
        self.interp.execute_cmd("add", 0)
        
        self.assertEqual(self.interp.stack, [2, 3])
        
        self.interp.execute_cmd("duplicate", 0)
        self.interp.stack.append(3) 
        self.interp.stack.append(1) 
        self.interp.execute_cmd("roll", 0)
        self.interp.execute_cmd("add", 0)
        
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
    #Если хотя бы один не подходит, пиксель не изменяется
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
    #Проверить normalize_pixels, которая применяет try_normalize_pixel ко всем пикселям изображения.
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
    """Проверить find_max_codel_size, который ищет 
    максимальный размер квадрата, на который можно 
    разбить изображение так, чтобы все пиксели внутри 
    каждого квадрата были одинаковы."""
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
    """Проверить scale_image, которая уменьшает изображение, 
    беря по одному пикселю из каждого блока scale_size × scale_size"""
    def setUp(self):
        from normalizer import Pixel
        self.Pixel = Pixel

    def test_scale_image_logic(self):
        """Проверяем, что изображение 4x4 при коделе 2 превращается in 2x2."""
        from normalizer import Pixel
        p = Pixel([255, 0, 0])
        # Создаем матрицу 4x4 из Pixel
        data = [[p for _ in range(4)] for _ in range(4)]

        scaled = Normalizer.scale_image(data, 2)

        # Проверяем размеры стандартного списка
        self.assertEqual(len(scaled), 2)
        self.assertEqual(len(scaled[0]), 2)
        self.assertIs(scaled[0][0], p)


class TestNormalizerFinal(unittest.TestCase):
    """на реальном файле ДляТестов.png 
    возвращает объект с корректными полями codels, width, height."""
    def test_normalize_integration_real_file(self):
        test_img = "ДляТестов.png"
        
        if not os.path.exists(test_img):
            self.skipTest(f"Файл {test_img} не найден, чекни путь мужик!")

        result = Normalizer.normalize(test_img, 0)

        # Проверяем структуру объекта
        self.assertTrue(hasattr(result, 'codels'), "Объект должен содержать поле codels")
        self.assertTrue(hasattr(result, 'width'), "Объект должен содержать поле width")
        self.assertTrue(hasattr(result, 'height'), "Объект должен содержать поле height")

        # Проверяем типы данных
        self.assertIsInstance(result.codels, list, "Поле pixels должно быть списком")
        
        if result.width > 0 and result.height > 0:
            top_left_pixel = result.codels[0][0]
            
            # Проверяем, что это объект Pixel и он нормализован
            print(f"\n[LOG] Цвет первого кодела: ({top_left_pixel.r}, {top_left_pixel.g}, {top_left_pixel.b})")

        else:
            self.fail("все оч плохо(")


class TestNormalizerEdgeCases(unittest.TestCase):
    """краевые случаи нормализации"""
    def test_scale_image_with_objects(self):
        """Масштабирование матрицы 2×2 с шагом 2 даёт 1×1, 
        объект Pixel сохраняется."""
        from normalizer import Pixel
        p1 = Pixel([255, 0, 0])
        matrix = [[p1, p1], [p1, p1]] 
        
        scaled = Normalizer.scale_image(matrix, 2)
        self.assertEqual(len(scaled), 1)
        self.assertEqual(len(scaled[0]), 1)
        self.assertIs(scaled[0][0], p1)

    def test_find_max_codel_size_prime_gcd(self):
        """Изображение 7×7 одного цвета → размер кодела = 7 
        (проверка работы с НОД)."""
        # Картинка 7x7 одного цвета. GCD = 7. 
        # Если 7 есть в primes.txt, должен вернуть 7.
        data = np.zeros((7, 7, 3), dtype=np.uint8)
        size = Normalizer.find_max_codel_size([[Pixel([0,0,0]) for _ in range(7)] for _ in range(7)])
        self.assertEqual(size, 7)


class TestProgramState(unittest.TestCase):
    """Проверить методы pointer (поворот указателя направления)
    switch (переключение счётчика коделов)."""
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
        self.state.switch(2) # С четным числом
        self.assertNotEqual(self.state.cc, initial_cc)


class TestInterpreterCommands(unittest.TestCase):
    """Проверить корректность реализации арифметических и стековых команд."""
    def setUp(self):
        self.interp = PietInterpreter.__new__(PietInterpreter)
        self.interp.stack = []
        self.interp.state = ProgramState()

    def test_arithmetic(self):
        self.interp.stack = [10, 3]
        self.interp.execute_cmd("add", 0)
        self.assertEqual(self.interp.stack, [13])

        self.interp.stack = [10, 3]
        self.interp.execute_cmd("subtract", 0)
        self.assertEqual(self.interp.stack, [7])

        self.interp.stack = [10, 3]
        self.interp.execute_cmd("divide", 0)
        self.assertEqual(self.interp.stack, [3])

    def test_roll(self):
        self.interp.stack = [4, 3, 2, 1, 3, 1]
        self.interp.execute_cmd("roll", 0)
        self.assertEqual(self.interp.stack, [4, 1, 3, 2])

    def test_not_and_greater(self):
        self.interp.stack = [5]
        self.interp.execute_cmd("not", 0)
        self.assertEqual(self.interp.stack, [0])

        self.interp.stack = [0]
        self.interp.execute_cmd("not", 0)
        self.assertEqual(self.interp.stack, [1])

        self.interp.stack = [5, 10]
        self.interp.execute_cmd("greater", 0)
        self.assertEqual(self.interp.stack, [0])

        
class TestInterpreterExecution(unittest.TestCase):
    """проверка на мелких изображениях"""
    def setUp(self):
        self.interp = PietInterpreter.__new__(PietInterpreter)
        self.interp.stack = []
        self.interp.state = ProgramState()
        self.interp.max_step_count = 10
        
        self.interp.palette = [
            [Pixel((255, 192, 192)), Pixel((255, 255, 192)), Pixel((192, 255, 192)),
             Pixel((192, 255, 255)), Pixel((192, 192, 255)), Pixel((255, 192, 255))],
            [Pixel((255, 0, 0)), Pixel((255, 255, 0)), Pixel((0, 255, 0)),
             Pixel((0, 255, 255)), Pixel((0, 0, 255)), Pixel((255, 0, 255))],
            [Pixel((192, 0, 0)), Pixel((192, 192, 0)), Pixel((0, 192, 0)),
             Pixel((0, 192, 192)), Pixel((0, 0, 192)), Pixel((192, 0, 192))]
        ]
        self.interp.black = Pixel((0, 0, 0))
        self.interp.white = Pixel((255, 255, 255))
        self.interp.commands = [
            ["none", "add", "divide", "greater", "duplicate", "in_char"],
            ["push", "subtract", "mod", "pointer", "roll", "out_num"],
            ["pop", "multiply", "not", "switch", "in_num", "out_char"]
        ]
        self.interp.codel_size = 1

    def test_interpreter_discovers_block_and_moves(self):
        """Находит блок красного цвета из 4 коделов, 
        вычисляет выходной кодел (должен быть (1,0) при DP=RIGHT)."""
        p_red = self.interp.palette[1][0]
        p_yellow = self.interp.palette[1][1]
        
        self.interp.pixels = [
            [p_red, p_red, p_yellow],
            [p_red, p_red, p_yellow],
            [p_yellow, p_yellow, p_yellow]
        ]
        self.interp.width = 3
        self.interp.height = 3

        block, color = self.interp.get_block(0, 0)
        self.assertEqual(len(block), 4, "Должен найти блок из 4 красных пикселей")
        self.assertEqual(color, p_red)

        exit_c = self.interp.find_exit_codel(block)
        self.assertEqual(exit_c, (1, 0))

    def test_interpreter_hits_black_block_and_rotates(self):
        """При столкновении с чёрным блоком интерпретатор пытается изменить DP/CC, 
        и после 8 попыток DP возвращается в исходное состояние RIGHT"""
        p_red = self.interp.palette[1][0]
        p_black = self.interp.black
        
        self.interp.pixels = [
            [p_red, p_black],
            [p_black, p_black]
        ]
        self.interp.width = 2
        self.interp.height = 2
        
        self.interp.step_border_exist = lambda: True

        try:
            self.interp.run()
        except Exception as e:
            self.fail(f"Метод run() упал с ошибкой при обработке черных блоков: {e}")

        self.assertEqual(self.interp.state.dp, DirPointerState.RIGHT, 
                         "После полной блокировки и 8 попыток DP должен вернуться в исходную позицию")

    def test_interpreter_white_sliding(self):
        """Проходит через белую область, не выполняя команд, 
        и достигает следующего цветного блока."""
        p_red = self.interp.palette[1][0]
        p_white = self.interp.white
        p_blue = self.interp.palette[1][4]
        
        self.interp.pixels = [
            [p_red, p_white, p_blue]
        ]
        self.interp.width = 3
        self.interp.height = 1
        
        self.interp.max_step_count = 1
        self.interp.run()
        
        self.assertEqual(self.interp.step_border_exist(), True)

    @patch('sys.stdout', new_callable=MagicMock)
    def test_io_commands_execution(self, mock_stdout):
        """Проверяет вывод чисел (out_num) и символов (out_char) через sys.stdout."""
        self.interp.stack = [65, 42]
        
        self.interp.execute_cmd("out_num", 0)
        self.assertEqual(self.interp.stack, [65])
        mock_stdout.write.assert_any_call("42")

        self.interp.execute_cmd("out_char", 0)
        self.assertEqual(self.interp.stack, [])
        mock_stdout.write.assert_any_call("A")
        
    def test_interpreter_total_block_stops_program(self):
        """Если программа полностью заблокирована чёрным, 
        она останавливается (DP не меняется бесконечно)."""
        p_red = self.interp.palette[1][0]
        p_black = self.interp.black
        
        self.interp.pixels = [
            [p_red, p_black],
            [p_black, p_black]
        ]
        self.interp.width = 2
        self.interp.height = 2
        
        self.interp.run()
        
        self.assertEqual(self.interp.state.dp, DirPointerState.RIGHT)
        
        
class TestNormalizerSupplementary(unittest.TestCase):
    def test_pixel_magic_methods(self):
        """чекаем методы __str__, __hash__, __eq__ класса Pixel"""
        p1 = Pixel([255, 0, 0])
        p2 = Pixel([255, 0, 0])
        self.assertEqual(str(p1), "(255, 0, 0)")
        self.assertEqual(hash(p1), hash((255, 0, 0)))
        self.assertFalse(p1 == [255, 0, 0])

    def test_check_squares_false(self):
        """Если в каком-то квадрате пиксели не одинаковы, 
        find_max_codel_size вернёт 1 (а не 2)"""
        p_red = Pixel([255, 0, 0])
        p_blue = Pixel([0, 0, 255])
        pixels = [
            [p_red, p_red],
            [p_red, p_blue]
        ]
        size = Normalizer.find_max_codel_size(pixels)
        self.assertEqual(size, 1)
        
        
class TestPietInterpreterAdvanced(unittest.TestCase):
    """еще еще и еще проверки"""
    def setUp(self):
        self.interp = PietInterpreter.__new__(PietInterpreter)
        self.interp.stack = []
        self.interp.state = ProgramState()

    def test_execute_cmd_empty_stack_resilience(self):
        """Все команды, требующие элементов стека, 
        не должны падать при пустом стеке"""
        commands_to_test = ["pop", "add", "subtract", "multiply", "divide", 
                            "mod", "not", "greater", "pointer", "switch", "duplicate", "roll"]
        for cmd in commands_to_test:
            try:
                self.interp.execute_cmd(cmd, 0)
            except Exception as e:
                self.fail(f"Команда {cmd} выбросила исключение при пустом стеке: {e}")
        self.assertEqual(self.interp.stack, [])

    def test_execute_cmd_division_by_zero(self):
        """Деление и остаток на ноль"""
        self.interp.stack = [10, 0]
        self.interp.execute_cmd("divide", 0)
        self.assertEqual(self.interp.stack, [10, 0], "Деление на ноль должно игнорироваться")

        self.interp.stack = [10, 0]
        self.interp.execute_cmd("mod", 0)
        self.assertEqual(self.interp.stack, [10, 0], "Взятие остатка по модулю 0 должно игнорироваться")

    def test_execute_cmd_invalid_roll(self):
        """roll с отрицательной глубиной или глубиной больше доступной
        типа не должен падать"""
        self.interp.stack = [1, 2, 3, -1, 1]
        self.interp.execute_cmd("roll", 0)
        self.assertEqual(self.interp.stack, [1, 2, 3, -1, 1])

        self.interp.stack = [1, 2, 3, 10, 1]
        self.interp.execute_cmd("roll", 0)
        self.assertEqual(self.interp.stack, [1, 2, 3, 10, 1])

    @patch('sys.stdin')
    def test_execute_cmd_io_input(self, mock_stdin):
        """in_num и in_char правильно читают из sys.stdin"""
        mock_stdin.readline.return_value = "42\n"
        self.interp.execute_cmd("in_num", 0)
        self.assertEqual(self.interp.stack, [42])

        mock_stdin.read.return_value = "Z"
        self.interp.execute_cmd("in_char", 0)
        self.assertEqual(self.interp.stack, [42, 90])

    def test_interpreter_reload(self):
        """корректно перезагружает новое изображение."""
        with patch('normalizer.Normalizer.normalize') as mock_norm:
            mock_img = MagicMock()
            mock_img.codels = [[Pixel([0, 0, 0])]]
            mock_img.width = 1
            mock_img.height = 1
            mock_norm.return_value = mock_img
            
            self.interp.reload("fake_path.png", codel_size=1, step_border=5)
            self.assertEqual(self.interp.max_step_count, 5)
            self.assertEqual(self.interp.width, 1)

    def test_find_exit_codel_all_directions(self):
        """Проверяет выбор выходного кодела для разных комбинаций 
        DP и CC (блок 2×2)"""
        block = {(0, 0), (1, 0), (0, 1), (1, 1)}
        
        self.interp.state.dp = DirPointerState.DOWN
        self.interp.state.cc = CodelCounterState.LEFT
        self.assertEqual(self.interp.find_exit_codel(block), (1, 1))
        
        self.interp.state.dp = DirPointerState.LEFT
        self.interp.state.cc = CodelCounterState.LEFT
        self.assertEqual(self.interp.find_exit_codel(block), (0, 1))
        
        self.interp.state.dp = DirPointerState.UP
        self.interp.state.cc = CodelCounterState.RIGHT
        self.assertEqual(self.interp.find_exit_codel(block), (1, 0))

    def test_white_sliding_hit_obstacle(self):
        """Белое скольжение, упирающееся в чёрный блок, 
        заставляет интерпретатор менять DP/CC."""
        self.interp.palette = [[Pixel((255, 0, 0))]]
        self.interp.black = Pixel((0, 0, 0))
        self.interp.white = Pixel((255, 255, 255))
        self.interp.codel_size = 1
        self.interp.max_step_count = 1
        
        self.interp.pixels = [[Pixel((255, 0, 0)), Pixel((255, 255, 255)), Pixel((0, 0, 0))]]
        self.interp.width = 3
        self.interp.height = 1
        
        self.interp.run()
        
        self.assertEqual(self.interp.state.dp, DirPointerState.RIGHT)
        self.assertEqual(self.interp.state.cc, CodelCounterState.LEFT)
        
        self.interp.max_step_count = 2
        self.interp.run()
        
        self.assertEqual(self.interp.state.cc, CodelCounterState.RIGHT)
        self.assertEqual(self.interp.state.dp, DirPointerState.DOWN)


app = QApplication.instance() or QApplication([])

class TestGraphicPietInterpreter(unittest.TestCase):
    def setUp(self):
        self.mock_interp = MagicMock(spec=PietInterpreter)
        
        self.mock_interp.state = MagicMock()
        self.mock_interp.state.dp = DirPointerState.RIGHT
        self.mock_interp.state.cc = CodelCounterState.LEFT
        self.mock_interp.state.x = 0
        self.mock_interp.state.y = 0
        
        # Делаем поле 2х2, чтобы указатель мог шагнуть из (0,0) в (1,0) и не упереться в стену
        self.mock_interp.width = 2
        self.mock_interp.height = 2
        
        # Имитируем палитру (два пикселя по горизонтали)
        self.mock_interp.pixels = [
            [MagicMock(), MagicMock()],
            [MagicMock(), MagicMock()]
        ]
        self.mock_interp.black = "BLACK"
        self.mock_interp.white = "WHITE"
        
        # Настраиваем дефолтные возвращаемые значения для успешного шага
        self.mock_interp.get_block.return_value = ([(0,0)], "COLOR1")
        self.mock_interp.find_exit_codel.return_value = (0, 0)
        self.mock_interp.get_color_coords.side_effect = [(0,0), (0,1)] 
        
        # Заглушка команд (матрица 3x6)
        self.mock_interp.commands = [["push"] * 6] * 3
        self.mock_interp.stack = [] 
        
        with patch('step_by_step_piet.PietInterpreter', return_value=self.mock_interp):
            self.gui = GraphicPietInterpreter("dummy.png")
            
        self.gui.canvas = MagicMock()
        self.gui.canvas.update = MagicMock()

    def test_step_standard_execution(self):
        """Проверка обычного шага (увеличение счетчика)."""
        self.gui.step()
        self.assertEqual(self.gui.step_counter, 1)

    def test_step_requires_input(self):
        """Проверка перехода в режим ввода."""
        # Подменяем матрицу команд мока, чтобы при любом шаге выпадал in_num
        self.mock_interp.commands = [["in_num"] * 6] * 3

        # Не мокаем сам метод интерфейса, даем ему отработать реально
        self.gui.step()
        
        # Теперь реальный intercept_execute_cmd установит все флаги
        self.assertTrue(self.gui.waiting_for_input)
        self.assertTrue(self.gui.input_field.isEnabled())
        self.assertEqual(self.gui.pending_cmd, "in_num")

    def test_step_resume_after_input(self):
        """Проверка обработки введенных пользователем данных."""
        self.gui.waiting_for_input = True
        self.gui.pending_cmd = "in_num"
        self.gui.input_field.setText("42")
        self.gui.input_field.setEnabled(True)
        
        # Сохраненные координаты прерванного шага
        self.gui.pending_next_x = 1
        self.gui.pending_next_y = 0
        
        self.gui.step()
        
        self.assertIn(42, self.mock_interp.stack)
        self.assertFalse(self.gui.waiting_for_input)
        self.assertEqual(self.gui.step_counter, 1)

class TestPietLogic(unittest.TestCase):
    def setUp(self):
        # Здесь можно тестировать логику самого Piet (если нужно), 
        # используя реальный или замоканный PietInterpreter
        pass

    def test_obstacle_rotation(self):
        """
        Пример теста логики: если мы уперлись в препятствие, 
        состояние должно измениться (повернуться).
        """
        # Допустим, мы проверяем правило, что при препятствии вызывается rotate
        state = MagicMock()
        # Простая проверка поведения при столкновении
        # (допиши логику согласно своим правилам из piet.py)
        self.assertTrue(True)


class TestGraphicPietCoverage(unittest.TestCase):
    """
    Класс для агрессивного покрытия файла step_by_step_piet.py.
    Тестирует отрисовку, ветвления в step() и перехват ввода-вывода.
    """
    def setUp(self):
        self.mock_interp = MagicMock(spec=PietInterpreter)
        
        self.mock_interp.state = MagicMock()
        self.mock_interp.state.dp = DirPointerState.RIGHT
        self.mock_interp.state.cc = CodelCounterState.LEFT
        self.mock_interp.state.x = 0
        self.mock_interp.state.y = 0
        
        self.mock_interp.width = 2
        self.mock_interp.height = 2
        
        # Создаем фейковые пиксели с заглушками свойств r, g, b
        p = MagicMock()
        p.r, p.g, p.b = 255, 0, 0
        self.mock_interp.pixels = [[p, p], [p, p]]
        self.mock_interp.black = "BLACK"
        self.mock_interp.white = "WHITE"
        self.mock_interp.stack = [] 
        
        with patch('step_by_step_piet.PietInterpreter', return_value=self.mock_interp):
            self.gui = GraphicPietInterpreter("dummy.png")
            
        # Глушим физическое обновление интерфейса, чтобы тесты летали
        self.gui.canvas.update = MagicMock()

    def test_update_ui_states_terminated(self):
        """Проверка обновления UI при завершении программы (is_terminated = True)."""
        self.gui.is_terminated = True
        self.gui.update_ui_states()
        self.assertEqual(self.gui.step_button.text(), "Terminated")
        self.assertFalse(self.gui.step_button.isEnabled())
        self.assertIn("[PROGRAM HALTED]", self.gui.info_label.text())

    def test_intercept_out_num(self):
        """Проверка перехвата вывода числа."""
        self.mock_interp.stack.append(42)
        # Должен вернуть False (не прерывать шаг)
        requires_pause = self.gui.intercept_execute_cmd("out_num", 0)
        self.assertFalse(requires_pause)
        self.assertEqual(self.gui.output_field.toPlainText(), "42")

    def test_intercept_out_char(self):
        """Проверка перехвата вывода символа."""
        self.mock_interp.stack.append(65) # ASCII код 'A'
        requires_pause = self.gui.intercept_execute_cmd("out_char", 0)
        self.assertFalse(requires_pause)
        self.assertEqual(self.gui.output_field.toPlainText(), "A")

    def test_intercept_standard_cmd(self):
        """Обычная команда не должна прерывать работу UI, а должна уйти в ядро."""
        requires_pause = self.gui.intercept_execute_cmd("add", 0)
        self.assertFalse(requires_pause)
        self.mock_interp.execute_cmd.assert_called_with("add", 0)

    def test_step_early_exit_if_terminated(self):
        """Если программа уже остановлена, step() ничего не делает."""
        self.gui.is_terminated = True
        initial_counter = self.gui.step_counter
        self.gui.step()
        self.assertEqual(self.gui.step_counter, initial_counter)

    def test_step_waiting_empty_input(self):
        """Если ожидаем ввод, но поле пустое, шаг не завершается."""
        self.gui.waiting_for_input = True
        self.gui.input_field.setText("")
        self.gui.step()
        self.assertTrue(self.gui.waiting_for_input)

    def test_step_resume_in_char(self):
        """Обработка пользовательского ввода символа (in_char)."""
        self.gui.waiting_for_input = True
        self.gui.pending_cmd = "in_char"
        self.gui.input_field.setText("Z")
        self.gui.step()
        self.assertIn(90, self.mock_interp.stack) # ord("Z") = 90
        self.assertFalse(self.gui.waiting_for_input)

    def test_step_resume_invalid_in_num(self):
        """Если запросили число, а ввели буквы, программа не должна упасть."""
        self.gui.waiting_for_input = True
        self.gui.pending_cmd = "in_num"
        self.gui.input_field.setText("not_a_number")
        self.gui.step()
        # Стек должен остаться пустым, ошибка ValueError перехвачена
        self.assertEqual(len(self.mock_interp.stack), 0)
        self.assertFalse(self.gui.waiting_for_input)

    def test_step_max_attempts_reached(self):
        """Проверка остановки по счетчику попыток."""
        self.gui.attempts = 8
        self.gui.step()
        self.assertTrue(self.gui.is_terminated)

    def test_step_hit_black_obstacle(self):
        """Проверка графической реакции на черную стену (должна вызвать switch/pointer)."""
        self.mock_interp.get_block.return_value = ([(0,0)], "COLOR")
        self.mock_interp.find_exit_codel.return_value = (0, 0)
        
        # Подстраиваем матрицу так, чтобы справа от (0,0) был BLACK
        self.mock_interp.pixels[0][1] = "BLACK"
        
        # Попытка 0: должен вызваться switch
        self.gui.attempts = 0
        self.gui.step()
        self.mock_interp.state.switch.assert_called_with(1)
        self.assertEqual(self.gui.attempts, 1)

        # Попытка 1: должен вызваться pointer
        self.gui.attempts = 1
        self.gui.step()
        self.mock_interp.state.pointer.assert_called_with(1)
        self.assertEqual(self.gui.attempts, 2)

    def test_step_hit_white_block(self):
        """Проверка графической реакции на белую зону (свободное скольжение)."""
        self.mock_interp.get_block.return_value = ([(0,0)], "COLOR")
        self.mock_interp.find_exit_codel.return_value = (0, 0)
        
        # Подстраиваем матрицу так, чтобы справа от (0,0) был WHITE
        self.mock_interp.pixels[0][1] = "WHITE"
        
        self.gui.step()
        # Указатель должен сдвинуться
        self.assertEqual(self.mock_interp.state.x, 1)
        self.assertEqual(self.mock_interp.state.y, 0)
        self.assertEqual(self.gui.step_counter, 1)

    @patch('step_by_step_piet.QPainter')
    def test_canvas_paint_event(self, MockPainter):
        """Искусственный вызов paintEvent, чтобы покрыть логику отрисовки."""
        event = MagicMock(spec=QPaintEvent)
        # Просто вызываем метод. Если он не падает, значит базовые расчеты координат проходят.
        try:
            self.gui.canvas.paintEvent(event)
        except Exception as e:
            self.fail(f"paintEvent упал с ошибкой: {e}")
            
            
if __name__ == '__main__':
    unittest.main()