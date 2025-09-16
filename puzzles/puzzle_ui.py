"""
This module is experimental and used to try out a basic UI to exercise
the PuzzlePy package. 
"""
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox, QVBoxLayout
import main
from main import Puzzle

class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Generate Soduku Puzzle")
        self.setGeometry(300, 300, 300, 200)

        self.button = QPushButton("Generate Puzzle", self)
        self.button.clicked.connect(self.on_click)

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        self.setLayout(layout)

    def on_click(self):
        status, flattened = Puzzle.generate_puzzle()
        if status ==  main.Status.PASSED:
            QMessageBox.information(self, "Puzzle Value", f"Puzzle = {flattened}")
        else:
            QMessageBox.information(self, "Message", f"Oooops, failed to generate puzzle!")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())
