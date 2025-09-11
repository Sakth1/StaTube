from UI.MainWindow import MainWindow
from PySide6.QtWidgets import QApplication
import traceback

try:
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()

except Exception as e:
    traceback.print_exc()
    print(e)