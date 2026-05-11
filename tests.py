import unittest
from piet import PietInterpreter, ProgramState
from normalizer import Normalizer

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
        from normalizer import Pixel
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


if __name__ == '__main__':
    unittest.main()