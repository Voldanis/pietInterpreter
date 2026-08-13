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

        painter.fillRect(self.rect(), QColor(40, 40, 40))

        if not self.interpreter.pixels:
            painter.end()
            return

        img_w = self.interpreter.width
        img_h = self.interpreter.height

        cell_w = self.width() / img_w
        cell_h = self.height() / img_h
        cell_size = min(cell_w, cell_h)

        offset_x = (self.width() - (img_w * cell_size)) / 2
        offset_y = (self.height() - (img_h * cell_size)) / 2

        for y in range(img_h):
            for x in range(img_w):
                pixel = self.interpreter.pixels[y][x]
                color = QColor(pixel.r, pixel.g, pixel.b)
                
                rect_x = offset_x + x * cell_size
                rect_y = offset_y + y * cell_size
                
                painter.fillRect(
                    QtCore.QRectF(rect_x, rect_y, cell_size, cell_size), 
                    color
                )
                
                if cell_size > 4:
                    painter.setPen(QPen(QColor(0, 0, 0, 25), 1))
                    painter.drawRect(QtCore.QRectF(rect_x, rect_y, cell_size, cell_size))

        state = self.interpreter.state
        if 0 <= state.x < img_w and 0 <= state.y < img_h:
            center_x = offset_x + state.x * cell_size + cell_size / 2
            center_y = offset_y + state.y * cell_size + cell_size / 2
            
            painter.save()
            painter.translate(center_x, center_y)
            
            if state.dp == DirPointerState.RIGHT:
                painter.rotate(0)
            elif state.dp == DirPointerState.DOWN:
                painter.rotate(90)
            elif state.dp == DirPointerState.LEFT:
                painter.rotate(180)
            elif state.dp == DirPointerState.UP:
                painter.rotate(270)

            arrow_size = max(cell_size * 0.8, 8.0)
            arrow = QPolygonF([
                QPointF(arrow_size / 2, 0),
                QPointF(-arrow_size / 2, -arrow_size / 3),
                QPointF(-arrow_size / 4, 0),
                QPointF(-arrow_size / 2, arrow_size / 3),
            ])

            pointer_color = QColor(255, 0, 100)
            painter.setPen(QPen(Qt.GlobalColor.black, 1.5))
            painter.setBrush(pointer_color)
            painter.drawPolygon(arrow)
            
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

        self.interpreter = PietInterpreter(image_path, codel_size)
        
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
        main_layout = QHBoxLayout()

        self.canvas = Canvas(self.interpreter)
        main_layout.addWidget(self.canvas, stretch=3)

        side_panel = QVBoxLayout()

        self.info_label = QLabel("Steps: 0\nDP: RIGHT | CC: LEFT\nLast Cmd: None")
        self.info_label.setFont(QFont("Courier New", 11))
        self.info_label.setStyleSheet("border: 1px solid #ccc; padding: 5px; background: #f9f9f9;")
        side_panel.addWidget(self.info_label)

        side_panel.addWidget(QLabel("Stack Control:"))
        self.stack_view = QTextEdit()
        self.stack_view.setReadOnly(True)
        self.stack_view.setFont(QFont("Courier New", 10))
        side_panel.addWidget(self.stack_view)

        self.input_label = QLabel("Input (Press Enter or Step to submit):")
        side_panel.addWidget(self.input_label)
        self.input_field = QLineEdit()
        self.input_field.setEnabled(False)
        self.input_field.returnPressed.connect(self.step)
        side_panel.addWidget(self.input_field)

        side_panel.addWidget(QLabel("Console Output:"))
        self.output_field = QTextEdit()
        self.output_field.setReadOnly(True)
        self.output_field.setFont(QFont("Courier New", 10))
        side_panel.addWidget(self.output_field)

        self.step_button = QPushButton("Step")
        self.step_button.setFixedHeight(35)
        self.step_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.step_button.clicked.connect(self.step)
        side_panel.addWidget(self.step_button)

        main_layout.addLayout(side_panel, stretch=1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        self.update_ui_states()

    def update_ui_states(self):
        state = self.interpreter.state
        dp_str = state.dp.name
        cc_str = state.cc.name
        
        status_text = (
            f"Steps: {self.step_counter}\n"
            f"DP: {dp_str} | CC: {cc_str}\n"
            f"Attempts: {self.attempts}/8\n"
            f"Last Cmd: {self.last_command}"
        )
        self.info_label.setText(status_text)

        self.stack_view.setText(f"Size: {len(self.interpreter.stack)}\n{str(self.interpreter.stack)}")

        if self.is_terminated:
            self.step_button.setText("Terminated")
            self.step_button.setEnabled(False)
            self.info_label.setText(status_text + "\n\n[PROGRAM HALTED]")

    def intercept_execute_cmd(self, cmd, n):
        self.last_command = f"{cmd} ({n})"

        if cmd in ("in_num", "in_char"):
            self.waiting_for_input = True
            self.pending_cmd = cmd
            self.pending_n = n
            self.input_field.setEnabled(True)
            self.input_field.setFocus()
            self.input_field.setStyleSheet("background-color: #fffacd;")
            return True

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

        self.interpreter.execute_cmd(cmd, n)
        return False

    def step(self):
        if self.is_terminated:
            return

        if self.waiting_for_input:
            input_text = self.input_field.text()
            if not input_text:
                return

            if self.pending_cmd == "in_num":
                try:
                    val = int(input_text.strip())
                    self.interpreter.stack.append(val)
                except ValueError:
                    pass
            elif self.pending_cmd == "in_char":
                if len(input_text) > 0:
                    self.interpreter.stack.append(ord(input_text[0]))

            self.waiting_for_input = False
            self.input_field.clear()
            self.input_field.setEnabled(False)
            self.input_field.setStyleSheet("")

            self.interpreter.state.x = self.pending_next_x
            self.interpreter.state.y = self.pending_next_y
            self.attempts = 0
            self.step_counter += 1
            
            self.canvas.update()
            self.update_ui_states()
            return

        if self.attempts >= 8:
            self.is_terminated = True
            self.update_ui_states()
            return

        state = self.interpreter.state
        block, color = self.interpreter.get_block(state.x, state.y)

        exit_codel = self.interpreter.find_exit_codel(block)
        dx, dy = DirPointerState.dp_to_delta(state.dp)
        new_x, new_y = exit_codel[0] + dx, exit_codel[1] + dy

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

        if next_color == self.interpreter.white:
            self.interpreter.state.x, self.interpreter.state.y = new_x, new_y
            self.attempts = 0
            self.step_counter += 1
            self.last_command = "Slide into White"
            self.canvas.update()
            self.update_ui_states()
            return

        color_coords = self.interpreter.get_color_coords(color)
        next_color_coords = self.interpreter.get_color_coords(next_color)

        if color_coords and next_color_coords:
            diff_light = (next_color_coords[0] - color_coords[0]) % 3
            diff_hue = (next_color_coords[1] - color_coords[1]) % 6
            cmd = self.interpreter.commands[diff_light][diff_hue]
            
            requires_pause = self.intercept_execute_cmd(cmd, len(block))
            if requires_pause:
                self.pending_next_x = new_x
                self.pending_next_y = new_y
                self.update_ui_states()
                return

        else:
            self.last_command = "None (Unknown Color)"

        self.interpreter.state.x, self.interpreter.state.y = new_x, new_y
        self.attempts = 0
        self.step_counter += 1
        
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