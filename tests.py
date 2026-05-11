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

if __name__ == '__main__':
    unittest.main()