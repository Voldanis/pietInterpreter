import sys
import numpy as np
from enum import Enum
from normalizer import *
from collections import deque

class DirPointerState(Enum):
    RIGHT = 0
    DOWN = 1
    LEFT = 2
    UP = 3

class CodelCounterState(Enum):
    LEFT = 0
    RIGHT = 1

class ProgramState:
    def __init__(self):
        self.dp = DirPointerState.RIGHT
        self.cc = CodelCounterState.LEFT

    def pointer(self, n):
        states = [DirPointerState.RIGHT,
                  DirPointerState.DOWN,
                  DirPointerState.LEFT,
                  DirPointerState.UP]
        # Поворот DP на n шагов по часовой стрелке
        change = (n + self.dp.value) % 4
        self.dp = states[change]

    def switch(self, n):
        states = [CodelCounterState.LEFT,
                  CodelCounterState.RIGHT]
        # Исправлено: переключение CC зависит от текущего CC, а не от DP
        change = (n + self.cc.value) % 2
        self.cc = states[change]

class PietInterpreter:
    def __init__(self, image_path, codel_size=-1, step_border=-1):
        img = Normalizer.normalize(image_path, codel_size)
        self.pixels = img.pixels
        self.width = img.width
        self.height = img.height
        self.codel_size = 1  # После нормализации работаем с коделом как с 1 пикселем
        self.step_border = step_border
        self.stack = []
        self.state = ProgramState()

        self.palette = [
            [(255, 192, 192), (255, 255, 192), (192, 255, 192), (192, 255, 255), (192, 192, 255), (255, 192, 255)],
            [(255, 0, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255), (255, 0, 255)],
            [(192, 0, 0), (192, 192, 0), (0, 192, 0), (0, 192, 192), (0, 0, 192), (192, 0, 192)]
        ]
        self.commands = [
            ["none", "add", "divide", "greater", "duplicate", "in_char"],
            ["push", "subtract", "mod", "pointer", "roll", "out_num"],
            ["pop", "multiply", "not", "switch", "in_num", "out_char"]
        ]

    def step_border_exist(self):
        return self.step_border >= 0

    def _get_color_coords(self, rgb):
        if isinstance(rgb, Pixel):
            rgb = (rgb.r, rgb.g, rgb.b)
        for l_idx, row in enumerate(self.palette):
            if rgb in row: return l_idx, row.index(rgb)
        return None

    def get_block(self, start_x, start_y):
        target_color = self.pixels[start_x][start_y]
        block = set()
        queue = deque([(start_x, start_y)])
        block.add((start_x, start_y))

        while queue:
            x, y = queue.popleft()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if (nx, ny) not in block and self.pixels[nx][ny] == target_color:
                        block.add((nx, ny))
                        queue.append((nx, ny))
        return block, target_color

    def _find_exit_codel(self, block):
        if self.state.dp == DirPointerState.RIGHT:
            mx = max(c[0] for c in block)
            edge = [c for c in block if c[0] == mx]
            edge.sort(key=lambda c: c[1], reverse=(self.state.cc == CodelCounterState.RIGHT))
        elif self.state.dp == DirPointerState.DOWN:
            my = max(c[1] for c in block)
            edge = [c for c in block if c[1] == my]
            edge.sort(key=lambda c: c[0], reverse=(self.state.cc == CodelCounterState.LEFT))
        elif self.state.dp == DirPointerState.LEFT:
            mx = min(c[0] for c in block)
            edge = [c for c in block if c[0] == mx]
            edge.sort(key=lambda c: c[1], reverse=(self.state.cc == CodelCounterState.LEFT))
        else: # UP
            my = min(c[1] for c in block)
            edge = [c for c in block if c[1] == my]
            edge.sort(key=lambda c: c[0], reverse=(self.state.cc == CodelCounterState.RIGHT))
        return edge[0]

    def _execute_cmd(self, cmd, n):
        try:
            if cmd == "push": self.stack.append(n)
            elif cmd == "pop":
                if self.stack: self.stack.pop()
            elif cmd == "add":
                if len(self.stack) >= 2: self.stack.append(self.stack.pop() + self.stack.pop())
            elif cmd == "subtract":
                if len(self.stack) >= 2:
                    a = self.stack.pop(); b = self.stack.pop()
                    self.stack.append(b - a)
            elif cmd == "multiply":
                if len(self.stack) >= 2: self.stack.append(self.stack.pop() * self.stack.pop())
            elif cmd == "divide":
                if len(self.stack) >= 2 and self.stack[-1] != 0:
                    a = self.stack.pop(); b = self.stack.pop()
                    self.stack.append(b // a)
            elif cmd == "mod":
                if len(self.stack) >= 2 and self.stack[-1] != 0:
                    a = self.stack.pop(); b = self.stack.pop()
                    self.stack.append(b % a)
            elif cmd == "not":
                if self.stack: self.stack.append(1 if self.stack.pop() == 0 else 0)
            elif cmd == "greater":
                if len(self.stack) >= 2:
                    a = self.stack.pop(); b = self.stack.pop()
                    self.stack.append(1 if b > a else 0)
            elif cmd == "pointer":
                if self.stack: self.state.pointer(self.stack.pop())
            elif cmd == "switch":
                if self.stack: self.state.switch(abs(self.stack.pop()))
            elif cmd == "duplicate":
                if self.stack: self.stack.append(self.stack[-1])
            elif cmd == "roll":
                if len(self.stack) >= 2:
                    count = self.stack.pop()
                    depth = self.stack.pop()
                    if depth > 0 and depth <= len(self.stack):
                        part = self.stack[-depth:]
                        rest = self.stack[:-depth]
                        shift = count % depth
                        if shift != 0:
                            part = part[-shift:] + part[:-shift]
                        self.stack = rest + part
            elif cmd == "in_num":
                res = sys.stdin.readline().strip()
                if res: self.stack.append(int(res))
            elif cmd == "in_char":
                char = sys.stdin.read(1)
                if char: self.stack.append(ord(char))
            elif cmd == "out_num":
                if self.stack: print(self.stack.pop(), end="", flush=True)
            elif cmd == "out_char":
                if self.stack: print(chr(self.stack.pop()), end="", flush=True)
        except Exception: pass

    def run(self):
        cx, cy = 0, 0
        attempts = 0
        step = 0

        while attempts < 8 and (not self.step_border_exist() or step < self.step_border):
            step += 1
            block, color = self.get_block(cx, cy)
            exit_c = self._find_exit_codel(block)
            
            # n = количество коделов в блоке
            nnnn = len(block)

            dx, dy = 0, 0
            if self.state.dp == DirPointerState.RIGHT: dx = 1
            elif self.state.dp == DirPointerState.DOWN: dy = 1
            elif self.state.dp == DirPointerState.LEFT: dx = -1
            elif self.state.dp == DirPointerState.UP: dy = -1

            nx, ny = exit_c[0] + dx, exit_c[1] + dy

            # Проверка препятствия
            is_obstacle = not (0 <= nx < self.width and 0 <= ny < self.height)
            if not is_obstacle:
                pixel = self.pixels[nx][ny]
                if isinstance(pixel, Pixel):
                    pixel = (pixel.r, pixel.g, pixel.b)
                if pixel == (0, 0, 0):
                    is_obstacle = True

            if is_obstacle:
                if attempts % 2 == 0: self.state.switch(1)
                else: self.state.pointer(1)
                attempts += 1
                continue

            next_pixel = self.pixels[nx][ny]
            if isinstance(next_pixel, Pixel):
                next_color = (next_pixel.r, next_pixel.g, next_pixel.b)
            else:
                next_color = next_pixel
            
            # Белый цвет (Slide)
            if next_color == (255, 255, 255):
                while 0 <= nx < self.width and 0 <= ny < self.height:
                    curr = self.pixels[nx][ny]
                    if isinstance(curr, Pixel): curr = (curr.r, curr.g, curr.b)
                    if curr != (255, 255, 255): break
                    nx += dx
                    ny += dy
                
                # Проверка того, куда выскочили из белого
                is_hit = not (0 <= nx < self.width and 0 <= ny < self.height)
                if not is_hit:
                    hit_p = self.pixels[nx][ny]
                    if isinstance(hit_p, Pixel): hit_p = (hit_p.r, hit_p.g, hit_p.b)
                    if hit_p == (0, 0, 0): is_hit = True
                
                if is_hit:
                    nx -= dx; ny -= dy
                    self.state.pointer(1)
                    attempts += 1
                    continue
                
                cx, cy = nx, ny
                attempts = 0
            else:
                c1 = self._get_color_coords(color)
                c2 = self._get_color_coords(next_color)
                
                if c1 and c2:
                    diff_light = (c2[0] - c1[0]) % 3
                    diff_hue = (c2[1] - c1[1]) % 6
                    cmd = self.commands[diff_light][diff_hue]
                    self._execute_cmd(cmd, nnnn)
                
                cx, cy = nx, ny
                attempts = 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python piet.py <file> <*size> <*step_border>")
    else:
        PietInterpreter(sys.argv[1],
                        int(sys.argv[2]) if len(sys.argv) > 2 else -1,
                        int(sys.argv[3]) if len(sys.argv) > 3 else -1).run()