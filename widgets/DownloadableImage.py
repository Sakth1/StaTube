# widgets/DownloadableImage.py
import os
from PySide6.QtWidgets import (
    QWidget, QFileDialog, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QButtonGroup, QRadioButton
)
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QIcon, QImage
from PySide6.QtCore import Qt, QSize


class ResolutionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Resolution")
        self.setMinimumWidth(260)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select export resolution:"))

        self.group = QButtonGroup(self)
        r1 = QRadioButton("1× Normal")
        r2 = QRadioButton("2× High")
        r3 = QRadioButton("4× Ultra")

        self.group.addButton(r1, 1)
        self.group.addButton(r2, 2)
        self.group.addButton(r3, 4)
        r2.setChecked(True)

        layout.addWidget(r1)
        layout.addWidget(r2)
        layout.addWidget(r3)

        btns = QHBoxLayout()
        ok = QPushButton("OK")
        cancel = QPushButton("Cancel")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addLayout(btns)

    def selected_scale(self):
        return self.group.checkedId()


class DownloadableImage(QWidget):
    """
    Auto-fits image to parent width.
    No horizontal scroll.
    Hover overlay for download.
    """

    def __init__(self, qimage: QImage, default_name="image.png", parent=None):
        super().__init__(parent)

        self.qimage = qimage
        self.default_name = default_name

        # Original HD pixmap
        self.full_pixmap = QPixmap.fromImage(qimage)

        # Display pixmap (scaled DOWN only)
        self.display_pixmap = self.full_pixmap

        self.hover = False
        self.setMouseTracking(True)

        self.icon = QIcon.fromTheme("download")

    def resizeEvent(self, event):
        """
        Always scale DOWN to fit width, never scale up.
        Ensures no horizontal scroll AND crisp image.
        """
        if not self.full_pixmap.isNull():
            target_width = min(self.width(), self.full_pixmap.width())
            self.display_pixmap = self.full_pixmap.scaledToWidth(
                target_width, Qt.SmoothTransformation
            )
            self.setMinimumHeight(self.display_pixmap.height())
        super().resizeEvent(event)

    def enterEvent(self, event):
        self.hover = True
        self.update()

    def leaveEvent(self, event):
        self.hover = False
        self.update()

    def mousePressEvent(self, event):
        if self.hover:
            self.save_image()

    def paintEvent(self, event):
        painter = QPainter(self)

        if not self.display_pixmap.isNull():
            painter.drawPixmap(0, 0, self.display_pixmap)

        if self.hover:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

            icon_size = 48
            x = (self.width() - icon_size) // 2
            y = (self.height() - icon_size) // 2

            if not self.icon.isNull():
                self.icon.paint(painter, x, y, icon_size, icon_size)
            else:
                painter.setPen(Qt.white)
                painter.setFont(QFont("Segoe UI", 24))
                painter.drawText(self.rect(), Qt.AlignCenter, "⬇")

    def sizeHint(self):
        return QSize(
            self.display_pixmap.width(),
            self.display_pixmap.height()
        )

    def save_image(self):
        dlg = ResolutionDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return

        scale = dlg.selected_scale()

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", self.default_name, "PNG Files (*.png)"
        )
        if not path:
            return

        export = self.qimage.scaled(
            self.qimage.width() * scale,
            self.qimage.height() * scale,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        export.save(path, "PNG")
