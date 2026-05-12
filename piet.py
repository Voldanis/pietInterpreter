import sys
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
        change = (n + self.dp.value) % 4
        self.dp = states[change]

    def switch(self, n):
        states = [CodelCounterState.LEFT,
                  CodelCounterState.RIGHT]
        change = (n + self.cc.value) % 2
        self.cc = states[change]


class PietInterpreter:
    def __init__(self, image_path, codel_size=-1, step_border=-1):
        img = Normalizer.normalize(image_path, codel_size)
        self.pixels = img.codels
        self.width = img.width
        self.height = img.height
        self.codel_size = 1  # удалить
        # Ограничитель шагов, чтобы не зависнуть вечно при тестах
        self.step_border = step_border
        self.stack = []
        self.state = ProgramState()

        self.palette = [
            [Pixel((255, 192, 192)), Pixel((255, 255, 192)), Pixel((192, 255, 192)),
             Pixel((192, 255, 255)), Pixel((192, 192, 255)), Pixel((255, 192, 255))],
            [Pixel((255, 0, 0)), Pixel((255, 255, 0)), Pixel((0, 255, 0)),
             Pixel((0, 255, 255)), Pixel((0, 0, 255)), Pixel((255, 0, 255))],
            [Pixel((192, 0, 0)), Pixel((192, 192, 0)), Pixel((0, 192, 0)),
             Pixel((0, 192, 192)), Pixel((0, 0, 192)), Pixel((192, 0, 192))]
        ]
        self.black = Pixel((0, 0, 0))
        self.white = Pixel((255, 255, 255))

        self.commands = [
            ["none", "add", "divide", "greater", "duplicate", "in_char"],
            ["push", "subtract", "mod", "pointer", "roll", "out_num"],
            ["pop", "multiply", "not", "switch", "in_num", "out_char"]
        ]

    # загрузить новое изображение
    def reload(self, image_path, codel_size=-1, step_border=-1):
        img = Normalizer.normalize(image_path, codel_size)
        self.pixels = img.codels
        self.width = img.width
        self.height = img.height
        self.codel_size = 1
        self.step_border = step_border
        self.stack = []
        self.state = ProgramState()

    def step_border_exist(self):
        return self.step_border >= 0

    def _get_color_coords(self, pixel):
        for row_i, row in enumerate(self.palette):
            if pixel in row:
                return row_i, row.index(pixel)
        return None

    def get_block(self, start_x, start_y):
        target_color = self.pixels[start_y][start_x]
        block = set()
        block.add((start_x, start_y))
        queue = deque()
        queue.append((start_x, start_y))

        while len(queue) > 0:
            x, y = queue.popleft()
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 or dy == 0:
                        nx = x + dx
                        ny = y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if (nx, ny) not in block and self.pixels[ny][nx] == target_color:
                                block.add((nx, ny))
                                queue.append((nx, ny))
        return block, target_color

    def _find_exit_codel(self, block):
        # Логика выбора кодела по DP/CC
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
        else: # Up
            my = min(c[1] for c in block)
            edge = [c for c in block if c[1] == my]
            edge.sort(key=lambda c: c[0], reverse=(self.state.cc == CodelCounterState.RIGHT))
        return edge[0]

    def _execute_cmd(self, cmd, n):
        try:
            if cmd == "push":
                self.stack.append(n)
            elif cmd == "pop":
                if self.stack:
                    self.stack.pop()
            elif cmd == "add":
                if len(self.stack) >= 2:
                    self.stack.append(self.stack.pop() + self.stack.pop())
            elif cmd == "subtract":
                if len(self.stack) >= 2:
                    a = self.stack.pop()
                    b = self.stack.pop()
                    self.stack.append(b - a)
            elif cmd == "multiply":
                if len(self.stack) >= 2:
                    self.stack.append(self.stack.pop() * self.stack.pop())
            elif cmd == "divide":
                if len(self.stack) >= 2 and self.stack[-1] != 0:
                    a = self.stack.pop()
                    b = self.stack.pop()
                    self.stack.append(b // a)
            elif cmd == "mod":
                if len(self.stack) >= 2 and self.stack[-1] != 0:
                    a = self.stack.pop()
                    b = self.stack.pop()
                    self.stack.append(b % a)
            elif cmd == "not":
                if self.stack:
                    self.stack.append(1 if self.stack.pop() == 0 else 0)
            elif cmd == "greater":
                if len(self.stack) >= 2:
                    a = self.stack.pop()
                    b = self.stack.pop()
                    self.stack.append(1 if b > a else 0)
            elif cmd == "pointer":
                if self.stack: self.state.pointer(self.stack.pop())
            elif cmd == "switch":
                if self.stack:
                    t = abs(self.stack.pop())
                    self.state.switch(t)
            elif cmd == "duplicate":
                if self.stack:
                    self.stack.append(self.stack[-1])
            elif cmd == "roll":
                if len(self.stack) >= 2:
                    count = self.stack.pop()
                    depth = self.stack.pop()
                    if 0 < depth <= len(self.stack):
                        part = self.stack[-depth:]
                        rest = self.stack[:-depth]
                        shift = count % depth
                        part = part[-shift:] + part[:-shift]
                        self.stack = rest + part
            elif cmd == "in_num":
                res = sys.stdin.readline().strip()
                if res:
                    self.stack.append(int(res))
            elif cmd == "in_char":
                char = sys.stdin.read(1)
                if char:
                    self.stack.append(ord(char))
            elif cmd == "out_num":
                if self.stack:
                    print(self.stack.pop(), end="", flush=True)
            elif cmd == "out_char":
                if self.stack:
                    print(chr(self.stack.pop()), end="", flush=True)
        except:
            pass

    def run(self):
        cx, cy = 0, 0
        attempts = 0
        step = 0

        while attempts < 8 and (not self.step_border_exist() or step < self.step_border):
            step += 1
            block, color = self.get_block(cx, cy)
            exit_c = self._find_exit_codel(block)

            # НОВЫЙ РАСЧЕТ РАЗМЕРА:
            # Мы считаем количество УНИКАЛЬНЫХ коделов в блоке.
            # Это спасет, если картинка чуть-чуть "кривая".
            unique_codels = set()
            for px, py in block:
                unique_codels.add((px // self.codel_size, py // self.codel_size))
            nnnn = len(unique_codels)

            # Определяем направление шага
            dx, dy = 0, 0
            if self.state.dp == DirPointerState.RIGHT:
                dx = self.codel_size
            elif self.state.dp == DirPointerState.DOWN:
                dy = self.codel_size
            elif self.state.dp == DirPointerState.LEFT:
                dx = -self.codel_size
            elif self.state.dp == DirPointerState.UP:
                dy = -self.codel_size

            nx, ny = exit_c[0] + dx, exit_c[1] + dy

            # Проверка столкновения (стена или черный)
            if not (0 <= nx < self.width and 0 <= ny < self.height) or self.pixels[ny][nx] == self.black:
                if attempts % 2 == 0:
                    self.state.switch(1)
                else:
                    self.state.pointer(1)
                attempts += 1
                continue

            next_color = self.pixels[ny][nx]

            # Обработка белого цвета (скольжение)
            if next_color == self.white:
                while 0 <= nx < self.width and 0 <= ny < self.height and self.pixels[ny][nx] == self.white:
                    nx += dx
                    ny += dy

                # Если после белого вылетели в стену или черный
                if not (0 <= nx < self.width and 0 <= ny < self.height) or self.pixels[ny][nx] == self.black:
                    # По спецификации: откатываемся назад в белый и меняем направление
                    nx -= dx
                    ny -= dy
                    self.state.pointer(1)
                    attempts += 1
                    # Важно: cx, cy остаются на входе в белый, просто пробуем другой выход
                    continue

                # Если нашли цвет после белого
                cx, cy = nx, ny
                attempts = 0
            else:
                # Обычный переход между цветами
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
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: python piet.py <file> <*size> <*step_border>")
    else:
        PietInterpreter(sys.argv[1],
                        int(sys.argv[2]) if len(sys.argv) > 2 else -1,
                        int(sys.argv[3]) if len(sys.argv) > 3 else -1).run()