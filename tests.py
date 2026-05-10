import unittest
from piet import PietInterpreter, ProgramState

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

if __name__ == '__main__':
    unittest.main()