import sys
from enum import Enum
from normalizer import *
from collections import deque


class DirPointerState(Enum):
    RIGHT = 0
    DOWN = 1
    LEFT = 2
    UP = 3

    @staticmethod
    def dp_to_delta(dp, cod_sise=1):
        if dp == DirPointerState.RIGHT:
            return cod_sise, 0
        elif dp == DirPointerState.DOWN:
            return 0, cod_sise
        elif dp == DirPointerState.LEFT:
            return -cod_sise, 0
        elif dp == DirPointerState.UP:
            return 0, -cod_sise


class CodelCounterState(Enum):
    LEFT = 0
    RIGHT = 1


class ProgramState:
    def __init__(self, dp=DirPointerState.RIGHT, cc=CodelCounterState.LEFT):
        self.dp = dp
        self.cc = cc

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

    def __copy__(self):
        return ProgramState(self.dp, self.cc)


class WhiteStates:
    def __init__(self):
        self.states = dict()

    def add_state(self, x, y, state):
        if x not in self.states.keys():
            self.states[x] = dict()
        if y not in self.states[x].keys():
            self.states[x][y] = []
        self.states[x][y].append(state.__copy__())

    def contains(self, x, y, state):
        if x not in self.states.keys() or y not in self.states[x].keys():
            return False
        for check in self.states[x][y]:
            if state.dp == check.dp and state.cc == check.cc:
                return True
        return False

    def clear(self):
        self.states = dict()


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

    def get_color_coords(self, pixel):
        for row_i, row in enumerate(self.palette):
            if pixel in row:
                return row_i, row.index(pixel)
        return None

    def get_block(self, start_x, start_y):
        target_color = self.pixels[start_y][start_x]
        if target_color == self.white:
            return {(start_x, start_y)}, target_color
        block = set()
        block.add((start_x, start_y))
        queue = deque()
        queue.append((start_x, start_y))

        while queue:
            x, y = queue.popleft()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if (nx, ny) not in block and self.pixels[ny][nx] == target_color:
                        block.add((nx, ny))
                        queue.append((nx, ny))
        return block, target_color

    def find_exit_codel(self, block):
        if self.state.dp == DirPointerState.RIGHT:
            max_x = max(c[0] for c in block)
            border_codels = [c for c in block if c[0] == max_x]
            border_codels.sort(key=lambda c: c[1], reverse=(self.state.cc == CodelCounterState.RIGHT))
        elif self.state.dp == DirPointerState.DOWN:
            max_y = max(c[1] for c in block)
            border_codels = [c for c in block if c[1] == max_y]
            border_codels.sort(key=lambda c: c[0], reverse=(self.state.cc == CodelCounterState.LEFT))
        elif self.state.dp == DirPointerState.LEFT:
            min_x = min(c[0] for c in block)
            border_codels = [c for c in block if c[0] == min_x]
            border_codels.sort(key=lambda c: c[1], reverse=(self.state.cc == CodelCounterState.LEFT))
        else:  # Up
            min_y = min(c[1] for c in block)
            border_codels = [c for c in block if c[1] == min_y]
            border_codels.sort(key=lambda c: c[0], reverse=(self.state.cc == CodelCounterState.RIGHT))
        return border_codels[0]

    def execute_cmd(self, cmd, n):
        try:
            if cmd == "push":
                self.stack.append(n)
            elif cmd == "pop":
                if len(self.stack) > 0:
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
                if len(self.stack) > 0:
                    self.stack.append(1 if self.stack.pop() == 0 else 0)
            elif cmd == "greater":
                if len(self.stack) >= 2:
                    a = self.stack.pop()
                    b = self.stack.pop()
                    self.stack.append(1 if b > a else 0)
            elif cmd == "pointer":
                if len(self.stack) > 0:
                    self.state.pointer(self.stack.pop())
            elif cmd == "switch":
                if len(self.stack) > 0:
                    t = abs(self.stack.pop())
                    self.state.switch(t)
            elif cmd == "duplicate":
                if len(self.stack) > 0:
                    self.stack.append(self.stack[-1])
            elif cmd == "roll":
                if len(self.stack) >= 2:
                    count = self.stack.pop()
                    depth = self.stack.pop()
                    if 0 < depth <= len(self.stack):
                        part = self.stack[-depth:]
                        rest = self.stack[:-depth]
                        shift = count % depth
                        if shift != 0:
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
                if len(self.stack) > 0:
                    print(self.stack.pop(), end="", flush=True)
            elif cmd == "out_char":
                if len(self.stack) > 0:
                    print(chr(self.stack.pop()), end="", flush=True)
            elif cmd == "none":
                pass
        except:
            pass

    def run(self):
        x, y = 0, 0
        attempts = 0
        step = 0
        white_states = WhiteStates()

        while attempts < 8 and (not self.step_border_exist() or step < self.step_border):
            step += 1
            block, color = self.get_block(x, y)
            if color == self.white:
                if white_states.contains(x, y, self.state):
                    return
                white_states.add_state(x, y, self.state)

            exit_codel = self.find_exit_codel(block)
            dx, dy = DirPointerState.dp_to_delta(self.state.dp)
            new_x, new_y = exit_codel[0] + dx, exit_codel[1] + dy


            # Проверка препятствия
            is_border = not (0 <= new_x < self.width and 0 <= new_y < self.height)
            if is_border or self.pixels[new_y][new_x] == self.black:
                if attempts % 2 == 0:
                    self.state.switch(1)
                else:
                    self.state.pointer(1)
                attempts += 1
                continue

            next_color = self.pixels[new_y][new_x]
            if next_color == self.white:
                if color != self.white:
                    white_states.clear()
                x, y = new_x, new_y
                attempts = 0
                continue

            # Обычный переход между цветами
            color_coords = self.get_color_coords(color)
            next_color_coords = self.get_color_coords(next_color)

            if color_coords and next_color_coords:
                diff_light = (next_color_coords[0] - color_coords[0]) % 3
                diff_hue = (next_color_coords[1] - color_coords[1]) % 6
                cmd = self.commands[diff_light][diff_hue]
                self.execute_cmd(cmd, len(block))

            x, y = new_x, new_y
            attempts = 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python piet.py <file> <*size> <*step_border>")
    else:
        PietInterpreter(sys.argv[1],
                        int(sys.argv[2]) if len(sys.argv) > 2 else -1,
                        int(sys.argv[3]) if len(sys.argv) > 3 else -1).run()