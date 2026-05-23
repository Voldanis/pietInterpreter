import sys
import subprocess

try:
    import PyQt6
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt6"])

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLineEdit, QTextEdit, QPushButton, QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QMouseEvent, QPaintEvent
from piet import PietInterpreter


class Canvas(QWidget):
    """
    Виджет, в котором рисуется программа.
    При вызове события paintEvent (например, когда вызывается метод canvas.update()) должно перерисовываться состояние
    программы.
    """
    def __init__(self, interpreter):
        super().__init__()
        self.interpreter = interpreter
        self.setMinimumSize(600, 400)  # нужно, чтобы автоматически подстраивался в зависимости от размеров width и heigth

    def paintEvent(self, event: QPaintEvent):
        #
        # Дописать. Класс содержит поле interpreter  в котором хранится PietInterpreter. Из него нужно достать pixels
        # и state и нарисовать их. Желательно, чтобы указатель на текущий блок был в виде стрелочки, которая указывает
        # в направлении dp. В state теперь хранятся текущие x, y
        #
        painter = QPainter(self)
        pen = QPen(Qt.GlobalColor.red, 2)  # цвет и размер контура
        painter.setPen(pen)
        painter.setBrush(Qt.GlobalColor.red)  # цвет заливки
        painter.fillRect(self.rect(), Qt.GlobalColor.white)  # цвет фона

        # рисуем кодел (x, y, ширина, высота)
        painter.drawRect(50, 50, 100, 100)
        # поменять цвет
        pen.setColor(Qt.GlobalColor.blue)
        painter.setPen(pen)
        painter.setBrush(Qt.GlobalColor.blue)
        # рисуем остальное ...
        painter.drawRect(150, 150, 100, 100)

        painter.end()


class GraphicPietInterpreter(QMainWindow):
    def __init__(self, image_path, codel_size=-1):
        super().__init__()
        self.setWindowTitle("Piet")
        self.setGeometry(100, 100, 800, 600)  # нужно, чтобы отрисовка изображения автоматически масштабировалась
        # в зависимости от размера окна

        self.interpreter = PietInterpreter(image_path, codel_size)
        layout = QVBoxLayout()

        self.canvas = Canvas(self.interpreter)
        layout.addWidget(self.canvas)

        self.step_button = QPushButton("Step")
        # self.setFixedSize(QSize(400, 300))
        self.step_button.setFixedSize(100, 25)
        # Вот так привязать вызов функции к кнопке
        # self.step_button.clicked.connect(self.step)
        layout.addWidget(self.step_button)

        # По хорошему стоит сделать label в котором будет писаться название последней выполненной команды

        # сделать, чтобы ввод-ввывод проходил через эти виджеты:
        input_label = QLabel("input")
        layout.addWidget(input_label)

        # делать активным для ввода только когда программа просит ввод
        self.input = QLineEdit()
        layout.addWidget(self.input)

        output_label = QLabel("output")
        layout.addWidget(output_label)

        # заблокировать для ввода
        self.output = QTextEdit()
        layout.addWidget(self.output)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def step(self):
        # ...
        self.canvas.update()


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python piet.py <file> <*codel_size>")
        print("* - optional")
    else:
        app = QApplication([])
        window = GraphicPietInterpreter(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else -1)
        window.show()
        app.exec()
