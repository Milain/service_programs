import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, QFileDialog,
                             QVBoxLayout, QWidget, QScrollArea, QLineEdit)
from PyQt5.QtGui import QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt, QPoint
from datetime import datetime


class ImageEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Динозавр-редактор")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.load_button = QPushButton("Выбрать картинку")
        self.load_button.clicked.connect(self.load_image)
        self.layout.addWidget(self.load_button)

        self.size_input = QLineEdit("200")
        self.size_input.setPlaceholderText("Размер области (пиксели)")
        self.layout.addWidget(self.size_input)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.mousePressEvent = self.on_image_click
        self.image_label.mouseMoveEvent = self.on_image_move
        self.image_label.mouseReleaseEvent = self.on_mouse_release
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        self.save_button = QPushButton("Создать обрезанную картинку")
        self.save_button.clicked.connect(self.save_cropped_image)
        self.layout.addWidget(self.save_button)

        self.original_pixmap = None
        self.display_pixmap = None
        self.center = None
        self.area_size = 200
        self.scale_factor = 1.0
        self.is_dragging = False

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Выбрать картинку", "", "Images (*.png *.jpg *.jpeg)")
        if file_name:
            self.original_pixmap = QPixmap(file_name)
            self.display_pixmap = self.original_pixmap.copy()
            self.scale_factor = 1.0
            self.center = None
            self.image_label.setPixmap(self.display_pixmap)
            self.image_label.adjustSize()

    def get_image_coords(self, event):
        """Вспомогательная функция для точного расчета координат"""
        if not self.original_pixmap:
            return None

        scroll_x = self.scroll_area.horizontalScrollBar().value()
        scroll_y = self.scroll_area.verticalScrollBar().value()
        label_pos = event.pos()

        pixmap_width = self.display_pixmap.width()
        pixmap_height = self.display_pixmap.height()
        label_width = self.image_label.width()
        label_height = self.image_label.height()

        # Вычисляем смещение изображения внутри label (центрирование)
        offset_x = max(0, (label_width - pixmap_width) // 2)
        offset_y = max(0, (label_height - pixmap_height) // 2)

        # Переводим координаты клика в координаты исходного изображения
        x = (label_pos.x() + scroll_x - offset_x) / self.scale_factor
        y = (label_pos.y() + scroll_y - offset_y) / self.scale_factor

        x = int(x)
        y = int(y)

        # Проверяем, что координаты в пределах изображения
        if 0 <= x < self.original_pixmap.width() and 0 <= y < self.original_pixmap.height():
            return QPoint(x, y)
        return None

    def on_image_click(self, event):
        coords = self.get_image_coords(event)
        if coords:
            self.center = coords
            self.area_size = int(self.size_input.text()) if self.size_input.text().isdigit() else 200
            self.is_dragging = True
            self.update_image()

    def on_image_move(self, event):
        if self.is_dragging:
            coords = self.get_image_coords(event)
            if coords:
                # Ограничиваем координаты, чтобы область не выходила за пределы
                x = max(self.area_size // 2, min(coords.x(), self.original_pixmap.width() - self.area_size // 2))
                y = max(self.area_size // 2, min(coords.y(), self.original_pixmap.height() - self.area_size // 2))
                self.center = QPoint(x, y)
                self.update_image()

    def on_mouse_release(self, event):
        self.is_dragging = False

    def update_image(self):
        if self.display_pixmap:
            pixmap_copy = self.display_pixmap.copy()
            painter = QPainter(pixmap_copy)

            if self.center:
                scaled_center = QPoint(int(self.center.x() * self.scale_factor),
                                       int(self.center.y() * self.scale_factor))
                painter.setPen(QPen(Qt.red, 5))
                painter.drawPoint(scaled_center)

                scaled_size = int(self.area_size * self.scale_factor)
                half_size = scaled_size // 2
                top_left = QPoint(scaled_center.x() - half_size, scaled_center.y() - half_size)
                painter.setPen(QPen(Qt.green, 2))
                painter.drawRect(top_left.x(), top_left.y(), scaled_size, scaled_size)

            painter.end()
            self.image_label.setPixmap(pixmap_copy)

    def save_cropped_image(self):
        if self.original_pixmap and self.center:
            half_size = self.area_size // 2
            cropped = self.original_pixmap.copy(self.center.x() - half_size,
                                                self.center.y() - half_size,
                                                self.area_size, self.area_size)
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"pic_cut_{current_time}.png"
            file_name, _ = QFileDialog.getSaveFileName(self, "Сохранить как", default_name, "Images (*.png *.jpg)")
            if file_name:
                cropped.save(file_name)
                print(f"Сохранено в {file_name}")

    def wheelEvent(self, event):
        if self.original_pixmap:
            scale = 1.1 if event.angleDelta().y() > 0 else 0.9
            self.scale_factor *= scale
            new_width = int(self.original_pixmap.width() * self.scale_factor)
            new_height = int(self.original_pixmap.height() * self.scale_factor)
            self.display_pixmap = self.original_pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio)
            self.update_image()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageEditor()
    window.show()
    sys.exit(app.exec_())