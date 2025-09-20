from UI.MainWindow import MainWindow
from PySide6.QtWidgets import QApplication

try:
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()

except Exception as e:
    import traceback
    traceback.print_exc()
    print(e)