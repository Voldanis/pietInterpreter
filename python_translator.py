# import sys
# from normalizer import Normalizer
from piet import *


class PietToPythonTranslator:
    def __init__(self, image_path: str, codel_size=-1):
        img = Normalizer.normalize(image_path, codel_size)
        self.pixels = img.codels
        self.width = img.width
        self.height = img.height
        # Ограничитель шагов, чтобы не зависнуть вечно при тестах
        self.stack = []
        self.state = ProgramState()
        self.program_name = image_path[image_path.rfind('/'):image_path.rfind('.')]

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

        self.command_names = [
            ["none", "add", "divide", "greater", "duplicate", "in_char"],
            ["push", "subtract", "mod", "pointer", "roll", "out_num"],
            ["pop", "multiply", "not", "switch", "in_num", "out_char"]
        ]

    def get_color_coords(self, pixel):
        """
        Получить индексы по которым можно получить данный pixel из palette
        """
        for row_i, row in enumerate(self.palette):
            if pixel in row:
                return row_i, row.index(pixel)
        return None

    def get_block(self, start_x, start_y):
        """
        Найти цветовой блок по содержащемуся в нем коделу.
        С помощью поиска в ширину находит все смежные коделы.
        """
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
        """
        Найти кодел из которого должен выйти интерпретатор в направлении dp
        """
        if self.state.dp == DirPointerState.RIGHT:
            max_x = max(c[0] for c in block)
            border_codels = [c for c in block if c[0] == max_x]
            # Вправо: лево - это вверх (min Y), право - это вниз (max Y)
            border_codels.sort(key=lambda c: c[1], reverse=(self.state.cc == CodelCounterState.RIGHT))
        elif self.state.dp == DirPointerState.DOWN:
            max_y = max(c[1] for c in block)
            border_codels = [c for c in block if c[1] == max_y]
            # Вниз: лево - это вправо (max X), право - это влево (min X)
            border_codels.sort(key=lambda c: c[0], reverse=(self.state.cc == CodelCounterState.LEFT))
        elif self.state.dp == DirPointerState.LEFT:
            min_x = min(c[0] for c in block)
            border_codels = [c for c in block if c[0] == min_x]
            # Влево: лево - это вниз (max Y), право - это вверх (min Y)
            border_codels.sort(key=lambda c: c[1], reverse=(self.state.cc == CodelCounterState.LEFT))
        else:  # Up
            min_y = min(c[1] for c in block)
            border_codels = [c for c in block if c[1] == min_y]
            # Вверх: лево - это влево (min X), право - это вправо (max X)
            border_codels.sort(key=lambda c: c[0], reverse=(self.state.cc == CodelCounterState.RIGHT))
        return border_codels[0]

    def execute_cmd(self, cmd, n, commands):
        if cmd == "push":
            commands.append("stack.append(" + str(n) + ")")
        elif cmd == "pop":
            commands.append("stack.pop()")
        elif cmd == "add":
            commands.append("stack.append(stack.pop() + stack.pop())")
        elif cmd == "subtract":
            commands.append("stack.append(stack.pop() - stack.pop())")
        elif cmd == "multiply":
            commands.append("stack.append(stack.pop() * stack.pop())")
        elif cmd == "divide":
            commands.append("stack.append(stack.pop() // stack.pop())")
        elif cmd == "mod":
            commands.append("stack.append(stack.pop() % stack.pop())")
        elif cmd == "not":
            commands.append("stack.append(1 if stack.pop() == 0 else 0)")
        elif cmd == "greater":
            commands.append("stack.append(1 if stack.pop() < stack.pop() else 0)")

        elif cmd == "duplicate":
            commands.append("stack.append(stack[-1])")
        elif cmd == "roll":
            commands.append("""
            count = stack.pop()
            depth = stack.pop()
            part = stack[-depth:]
            rest = stack[:-depth]
            shift = count % depth
            if shift != 0:
                part = part[-shift:] + part[:-shift]
            stack = rest + part
            """)
        elif cmd == "in_char":
            commands.append("stack.append(ord(input()[0]))")
        elif cmd == "in_num":
            commands.append("stack.append(int(input()))")
        elif cmd == "out_char":
            commands.append("print(chr(stack.pop()), end='')")
        elif cmd == "out_num":
            commands.append("print(stack.pop(), end='')")
        elif cmd == "pointer":
            raise NotImplementedError("not support 'pointer'")
        elif cmd == "switch":
            raise NotImplementedError("not support 'switch'")
        else:
            raise NotImplementedError("Неизвестная команда Piet")

    def translate(self):
        attempts = 0
        white_states = WhiteStates()
        commands = []

        # Проходимся по картине, пока не попали в тупик
        while attempts < 8:
            block, color = self.get_block(self.state.x, self.state.y)
            # Если мы на белом блоке, занести текущее состояние, чтобы потом проверить, не ходим ли мы кругами
            if color == self.white:
                if white_states.contains(self.state.x, self.state.y, self.state):
                    return
                white_states.add_state(self.state.x, self.state.y, self.state)

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
            # обработка белого цвета
            if next_color == self.white:
                if color != self.white:
                    white_states.clear()
                self.state.x, self.state.y = new_x, new_y
                attempts = 0
                continue

            # Обычный переход между цветами
            color_coords = self.get_color_coords(color)
            next_color_coords = self.get_color_coords(next_color)

            if color_coords and next_color_coords:
                diff_light = (next_color_coords[0] - color_coords[0]) % 3
                diff_hue = (next_color_coords[1] - color_coords[1]) % 6
                cmd = self.command_names[diff_light][diff_hue]
                self.execute_cmd(cmd, len(block), commands)

            self.state.x, self.state.y = new_x, new_y
            attempts = 0

        # перевод программы
        with open("python_programs/" + self.program_name + '.py', "w") as f:
            f.write('stack = []\n')
            for c in commands:
                f.write(c + '\n')


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python python_translator.py <file> <*codel_size>")
        print("* - optional")
    else:
        PietToPythonTranslator(sys.argv[1],
                        int(sys.argv[2]) if len(sys.argv) > 2 else -1).translate()
