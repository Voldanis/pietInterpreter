import sys
import subprocess

try:
    from PyQt6 import QtCore, QtGui, QtWidgets
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt6"])
    from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QPushButton, QLabel)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QPolygonF, QFont
from piet import PietInterpreter, DirPointerState, CodelCounterState


class Canvas(QWidget):
    """
    Виджет, в котором отрисовывается текущее состояние программы Piet.
    Масштабирует сетку коделов под размеры окна и рисует указатель интерпретатора.
    """
    def __init__(self, interpreter):
        super().__init__()
        self.interpreter = interpreter
        self.setMinimumSize(400, 400)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Очищаем фон (заливаем серым цветом для контраста с белыми коделами)
        painter.fillRect(self.rect(), QColor(40, 40, 40))

        if not self.interpreter.pixels:
            painter.end()
            return

        img_w = self.interpreter.width
        img_h = self.interpreter.height

        # Вычисляем динамический размер кодела с сохранением пропорций
        cell_w = self.width() / img_w
        cell_h = self.height() / img_h
        cell_size = min(cell_w, cell_h)

        # Центрируем изображение на холсте
        offset_x = (self.width() - (img_w * cell_size)) / 2
        offset_y = (self.height() - (img_h * cell_size)) / 2

        # 1. Отрисовка сетки коделов
        for y in range(img_h):
            for x in range(img_w):
                pixel = self.interpreter.pixels[y][x]
                color = QColor(pixel.r, pixel.g, pixel.b)
                
                rect_x = offset_x + x * cell_size
                rect_y = offset_y + y * cell_size
                
                # Рисуем кодел
                painter.fillRect(
                    QtCore.QRectF(rect_x, rect_y, cell_size, cell_size), 
                    color
                )
                
                # Легкая сетка для разделения коделов, если они достаточно крупные
                if cell_size > 4:
                    painter.setPen(QPen(QColor(0, 0, 0, 25), 1))
                    painter.drawRect(QtCore.QRectF(rect_x, rect_y, cell_size, cell_size))

        # 2. Отрисовка указателя текущего состояния (Стрелочка)
        state = self.interpreter.state
        if 0 <= state.x < img_w and 0 <= state.y < img_h:
            # Вычисляем центр текущего кодела
            center_x = offset_x + state.x * cell_size + cell_size / 2
            center_y = offset_y + state.y * cell_size + cell_size / 2
            
            painter.save()
            painter.translate(center_x, center_y)
            
            # Поворачиваем сцену в зависимости от направления DP
            if state.dp == DirPointerState.RIGHT:
                painter.rotate(0)
            elif state.dp == DirPointerState.DOWN:
                painter.rotate(90)
            elif state.dp == DirPointerState.LEFT:
                painter.rotate(180)
            elif state.dp == DirPointerState.UP:
                painter.rotate(270)

            # Формируем красивую стрелку, соразмерную коделу
            arrow_size = max(cell_size * 0.8, 8.0)
            arrow = QPolygonF([
                QPointF(arrow_size / 2, 0),
                QPointF(-arrow_size / 2, -arrow_size / 3),
                QPointF(-arrow_size / 4, 0),
                QPointF(-arrow_size / 2, arrow_size / 3),
            ])

            # Задаем контрастный контур и заливку (малиновый/ярко-красный)
            pointer_color = QColor(255, 0, 100)
            painter.setPen(QPen(Qt.GlobalColor.black, 1.5))
            painter.setBrush(pointer_color)
            painter.drawPolygon(arrow)
            
            # Дополнительный индикатор Codel Counter (CC) в хвосте стрелки
            # Если CC = LEFT, рисуем синюю точку слева от оси движения, если RIGHT — справа
            cc_offset = arrow_size / 3
            cc_y = -cc_offset if state.cc == CodelCounterState.LEFT else cc_offset
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 150, 255))
            painter.drawEllipse(QPointF(-arrow_size / 4, cc_y), arrow_size / 6, arrow_size / 6)

            painter.restore()

        painter.end()


class GraphicPietInterpreter(QMainWindow):
    def __init__(self, image_path, codel_size=-1):
        super().__init__()
        self.setWindowTitle("Piet Visual Debugger")
        self.setGeometry(100, 100, 900, 650)

        # Инициализируем оригинальный интерпретатор
        self.interpreter = PietInterpreter(image_path, codel_size)
        
        # Переменные для отслеживания истории выполнения в UI
        self.last_command = "None"
        self.attempts = 0
        self.step_counter = 0
        self.is_terminated = False
        self.waiting_for_input = False
        self.pending_cmd = None
        self.pending_n = 0
        self.pending_next_x = 0
        self.pending_next_y = 0

        self.init_ui()

    def init_ui(self):
        # Основной горизонтальный слой: слева холст, справа панель управления
        main_layout = QHBoxLayout()

        # Левая часть — Холст
        self.canvas = Canvas(self.interpreter)
        main_layout.addWidget(self.canvas, stretch=3)

        # Правая часть — Панель отладки
        side_panel = QVBoxLayout()

        # Информационный блок
        self.info_label = QLabel("Steps: 0\nDP: RIGHT | CC: LEFT\nLast Cmd: None")
        self.info_label.setFont(QFont("Courier New", 11))
        self.info_label.setStyleSheet("border: 1px solid #ccc; padding: 5px; background: #f9f9f9;")
        side_panel.addWidget(self.info_label)

        # Стек
        side_panel.addWidget(QLabel("Stack Control:"))
        self.stack_view = QTextEdit()
        self.stack_view.setReadOnly(True)
        self.stack_view.setFont(QFont("Courier New", 10))
        side_panel.addWidget(self.stack_view)

        # Поле ввода (заблокировано по умолчанию, активируется при запросе данных)
        self.input_label = QLabel("Input (Press Enter or Step to submit):")
        side_panel.addWidget(self.input_label)
        self.input_field = QLineEdit()
        self.input_field.setEnabled(False)
        self.input_field.returnPressed.connect(self.step)
        side_panel.addWidget(self.input_field)

        # Вывод программы
        side_panel.addWidget(QLabel("Console Output:"))
        self.output_field = QTextEdit()
        self.output_field.setReadOnly(True)
        self.output_field.setFont(QFont("Courier New", 10))
        side_panel.addWidget(self.output_field)

        # Кнопка шага
        self.step_button = QPushButton("Step")
        self.step_button.setFixedHeight(35)
        self.step_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.step_button.clicked.connect(self.step)
        side_panel.addWidget(self.step_button)

        main_layout.addLayout(side_panel, stretch=1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        # Обновляем UI под начальное состояние
        self.update_ui_states()

    def update_ui_states(self):
        """Синхронизирует данные из ядра PietInterpreter с графическими виджетами."""
        state = self.interpreter.state
        dp_str = state.dp.name
        cc_str = state.cc.name
        
        # Обновление текстовой метки
        status_text = (
            f"Steps: {self.step_counter}\n"
            f"DP: {dp_str} | CC: {cc_str}\n"
            f"Attempts: {self.attempts}/8\n"
            f"Last Cmd: {self.last_command}"
        )
        self.info_label.setText(status_text)

        # Обновление отображения стека
        self.stack_view.setText(f"Size: {len(self.interpreter.stack)}\n{str(self.interpreter.stack)}")

        if self.is_terminated:
            self.step_button.setText("Terminated")
            self.step_button.setEnabled(False)
            self.info_label.setText(status_text + "\n\n[PROGRAM HALTED]")

    def intercept_execute_cmd(self, cmd, n):
        """
        Перехватывает стандартное выполнение команд ввода-вывода,
        чтобы они корректно работали в GUI-потоке вместо sys.stdin/sys.stdout.
        """
        self.last_command = f"{cmd} ({n})"

        # Перехват Ввода
        if cmd in ("in_num", "in_char"):
            self.waiting_for_input = True
            self.pending_cmd = cmd
            self.pending_n = n
            self.input_field.setEnabled(True)
            self.input_field.setFocus()
            self.input_field.setStyleSheet("background-color: #fffacd;") # Подсвечиваем желтым
            return True # Требуется приостановка

        # Перехват Вывода
        if cmd == "out_num":
            if len(self.interpreter.stack) > 0:
                val = self.interpreter.stack.pop()
                self.output_field.insertPlainText(str(val))
                self.output_field.ensureCursorVisible()
            return False
        elif cmd == "out_char":
            if len(self.interpreter.stack) > 0:
                val = self.interpreter.stack.pop()
                try:
                    self.output_field.insertPlainText(chr(val))
                except ValueError:
                    pass
                self.output_field.ensureCursorVisible()
            return False

        # Все остальные стандартные команды выполняем через оригинальное ядро
        self.interpreter.execute_cmd(cmd, n)
        return False

    def step(self):
        """
        Осуществляет один шаг выполнения программы Piet.
        Восстановленный метод.
        """
        if self.is_terminated:
            return

        # 1. Обработка прерванного шага (ожидание ввода от пользователя)
        if self.waiting_for_input:
            input_text = self.input_field.text()
            if not input_text:
                return  # Ничего не ввели — ждем дальше

            if self.pending_cmd == "in_num":
                try:
                    val = int(input_text.strip())
                    self.interpreter.stack.append(val)
                except ValueError:
                    pass  # Если ввели не число, игнорируем (как в консоли)
            elif self.pending_cmd == "in_char":
                if len(input_text) > 0:
                    self.interpreter.stack.append(ord(input_text[0]))

            # Возвращаем интерфейс в обычное состояние
            self.waiting_for_input = False
            self.input_field.clear()
            self.input_field.setEnabled(False)
            self.input_field.setStyleSheet("")

            # Завершаем начатый шаг: передвигаем указатель на вычисленные ранее координаты
            self.interpreter.state.x = self.pending_next_x
            self.interpreter.state.y = self.pending_next_y
            self.attempts = 0
            self.step_counter += 1
            
            self.canvas.update()
            self.update_ui_states()
            return

        # 2. Базовое условие остановки по попыткам (из оригинального while attempts < 8)
        if self.attempts >= 8:
            self.is_terminated = True
            self.update_ui_states()
            return

        state = self.interpreter.state
        block, color = self.interpreter.get_block(state.x, state.y)

        # Логика обработки белого цвета (проверка зацикливания убрана для простоты шага, 
        # но навигация сохранена)
        exit_codel = self.interpreter.find_exit_codel(block)
        dx, dy = DirPointerState.dp_to_delta(state.dp)
        new_x, new_y = exit_codel[0] + dx, exit_codel[1] + dy

        # Проверка препятствия / Черного цвета
        is_border = not (0 <= new_x < self.interpreter.width and 0 <= new_y < self.interpreter.height)
        if is_border or self.interpreter.pixels[new_y][new_x] == self.interpreter.black:
            if self.attempts % 2 == 0:
                self.interpreter.state.switch(1)
            else:
                self.interpreter.state.pointer(1)
            self.attempts += 1
            self.last_command = "Obstacle (Rotate DP/CC)"
            self.canvas.update()
            self.update_ui_states()
            return

        next_color = self.interpreter.pixels[new_y][new_x]

        # Обработка перехода на белый цвет
        if next_color == self.interpreter.white:
            self.interpreter.state.x, self.interpreter.state.y = new_x, new_y
            self.attempts = 0
            self.step_counter += 1
            self.last_command = "Slide into White"
            self.canvas.update()
            self.update_ui_states()
            return

        # Обычный переход между стандартными цветами палитры
        color_coords = self.interpreter.get_color_coords(color)
        next_color_coords = self.interpreter.get_color_coords(next_color)

        if color_coords and next_color_coords:
            diff_light = (next_color_coords[0] - color_coords[0]) % 3
            diff_hue = (next_color_coords[1] - color_coords[1]) % 6
            cmd = self.interpreter.commands[diff_light][diff_hue]
            
            # Проверяем, требует ли команда интерактивного ввода
            requires_pause = self.intercept_execute_cmd(cmd, len(block))
            if requires_pause:
                # Сохраняем координаты, куда шагнет указатель ПОСЛЕ получения данных
                self.pending_next_x = new_x
                self.pending_next_y = new_y
                self.update_ui_states()
                return

        else:
            self.last_command = "None (Unknown Color)"

        # Смена координат при обычном успешном шаге
        self.interpreter.state.x, self.interpreter.state.y = new_x, new_y
        self.attempts = 0
        self.step_counter += 1
        
        # Обновляем графику
        self.canvas.update()
        self.update_ui_states()


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python step_by_step_piet.py <file> <*codel_size>")
        print("* - optional")
    else:
        app = QApplication([])
        window = GraphicPietInterpreter(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else -1)
        window.show()
        app.exec()