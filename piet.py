import sys
from PIL import Image
import numpy as np
from normalizer import *


class ProgramState:
    def __init__(self):
        self.dp = 0  # 0:R, 1:D, 2:L, 3:U
        self.cc = 0  # 0:L, 1:R


class PietInterpreter:
    def __init__(self, image_path, codel_size=-1, step_border=-1):
        img = Normalizer.normalize(image_path, codel_size)
        self.pixels = img.codels
        self.width = img.width
        self.height = img.height
        self.codel_size = 1
        self.stack = []
        self.state = ProgramState()
        # Ограничитель шагов, чтобы не зависнуть вечно при тестах
        self.step_border = step_border

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

    def reload(self):
        pass

    @staticmethod
    def max_square_size(image_path):
        """
        Оптимизированная версия с использованием NumPy.
        """
        with Image.open(image_path) as img:
            img.load()
            rgb_img = img.convert("RGB")
            pixel_array = np.array(rgb_img)

        height, width = pixel_array.shape[:2]

        # Находим все делители минимальной стороны
        min_dim = min(height, width)

        # Проверяем возможные размеры (только делители)
        for size in range(min_dim, 0, -1):
            if height % size == 0 and width % size == 0:
                if PietInterpreter.check_uniform_squares(pixel_array, size):
                    return size
        return 1

    @staticmethod
    def check_uniform_squares(pixel_array, square_size):
        """
        Быстрая проверка квадратов с использованием reshape.
        """
        height, width = pixel_array.shape[:2]

        # Изменяем форму массива для удобной проверки
        h_blocks = height // square_size
        w_blocks = width // square_size

        # Перестраиваем массив для группировки по блокам
        reshaped = pixel_array.reshape(h_blocks, square_size, w_blocks, square_size, -1)

        # Для каждого блока проверяем, что все элементы одинаковы
        for i in range(h_blocks):
            for j in range(w_blocks):
                block = reshaped[i, :, j, :, :]
                if not np.all(block == block[0, 0]):
                    return False

        return True

    def step_border_exist(self):
        return self.step_border >= 0

    def _get_color_coords(self, pixel):
        for l_idx, row in enumerate(self.palette):
            if pixel in row:
                return l_idx, row.index(pixel)
        return None

    def _get_block(self, start_x, start_y):
        """Оптимизированный Flood Fill: шагает сразу по коделам."""
        target_color = self.pixels[start_y][start_x]
        block = set()
        queue = [(start_x, start_y)]
        block.add((start_x, start_y))

        idx = 0
        while idx < len(queue):
            x, y = queue[idx]
            idx += 1
            # Проверяем соседей, отступая на размер кодела
            for dx, dy in [(self.codel_size, 0), (-self.codel_size, 0), (0, self.codel_size), (0, -self.codel_size)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if (nx, ny) not in block and self.pixels[ny][nx] == target_color:
                        block.add((nx, ny))
                        queue.append((nx, ny))
        return block, target_color

    def _find_exit_codel(self, block):
        # Логика выбора кодела по DP/CC
        if self.state.dp == 0:  # Right
            mx = max(c[0] for c in block)
            edge = [c for c in block if c[0] == mx]
            edge.sort(key=lambda c: c[1], reverse=(self.state.cc == 1))
        elif self.state.dp == 1:  # Down
            my = max(c[1] for c in block)
            edge = [c for c in block if c[1] == my]
            edge.sort(key=lambda c: c[0], reverse=(self.state.cc == 0))
        elif self.state.dp == 2:  # Left
            mx = min(c[0] for c in block)
            edge = [c for c in block if c[0] == mx]
            edge.sort(key=lambda c: c[1], reverse=(self.state.cc == 0))
        else:  # Up
            my = min(c[1] for c in block)
            edge = [c for c in block if c[1] == my]
            edge.sort(key=lambda c: c[0], reverse=(self.state.cc == 1))
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
                if self.stack:
                    self.state.dp = (self.state.dp + self.stack.pop()) % 4
            elif cmd == "switch":
                if self.stack:
                    t = abs(self.stack.pop())
                    for _ in range(t):
                        self.state.cc = 1 - self.state.cc
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
            block, color = self._get_block(cx, cy)
            exit_c = self._find_exit_codel(block)

            # НОВЫЙ РАСЧЕТ РАЗМЕРА:
            # Мы считаем количество УНИКАЛЬНЫХ коделов в блоке.
            # Это спасет, если картинка чуть-чуть "кривая".
            unique_codels = set()
            for px, py in block:
                unique_codels.add((px // self.codel_size, py // self.codel_size))
            n = len(unique_codels)

            # Определяем направление шага
            dx, dy = 0, 0
            if self.state.dp == 0:
                dx = self.codel_size
            elif self.state.dp == 1:
                dy = self.codel_size
            elif self.state.dp == 2:
                dx = -self.codel_size
            elif self.state.dp == 3:
                dy = -self.codel_size

            nx, ny = exit_c[0] + dx, exit_c[1] + dy

            # Проверка столкновения (стена или черный)
            if not (0 <= nx < self.width and 0 <= ny < self.height) or self.pixels[ny][nx] == self.black:
                if attempts % 2 == 0:
                    self.state.cc = 1 - self.state.cc
                else:
                    self.state.dp = (self.state.dp + 1) % 4
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
                    self.state.dp = (self.state.dp + 1) % 4
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
                    self._execute_cmd(cmd, n)

                cx, cy = nx, ny
                attempts = 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python piet.py <file> <size>")
    else:
        PietInterpreter(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1).run()