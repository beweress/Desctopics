import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# Функция для работы с путями в EXE-режиме
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AnimationWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                          Qt.WindowType.WindowStaysOnTopHint | 
                          Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        self.animation_frames = []
        self.current_frame_index = 0
        self.animation_speed = 100  # ms
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.next_frame)
        self.oldPos = None
        self.animation_loaded = False
        self.current_movie = None  # Для обработки GIF-файлов
        self.base_gif_speed = 100  # Базовая скорость для GIF (100 мс)

    def load_animation(self, file_paths):
        """Загружает анимацию: последовательность PNG или одиночный GIF"""
        # Останавливаем предыдущую анимацию
        if self.current_movie:
            self.current_movie.stop()
            self.current_movie = None
            
        if self.animation_timer.isActive():
            self.animation_timer.stop()
        
        # Сохраняем текущую позицию окна
        current_pos = self.pos()
        
        # Получаем размеры экрана
        screen = QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        max_width = screen_geo.width() * 0.9  # 90% ширины экрана
        max_height = screen_geo.height() * 0.9  # 90% высоты экрана
        
        self.animation_frames = []
        self.animation_loaded = False
        
        # Если передан один файл и он GIF
        if len(file_paths) == 1 and file_paths[0].lower().endswith('.gif'):
            self.load_gif_animation(file_paths[0], max_width, max_height)
        else:
            self.load_png_sequence(file_paths, max_width, max_height)
        
        if self.animation_loaded:
            self.adjustSize()
            self.move(current_pos)
            self.show()

    def load_png_sequence(self, file_paths, max_width, max_height):
        """Загружает последовательность PNG-файлов"""
        self.animation_frames = []
        
        for path in file_paths:
            # Используем resource_path для совместимости с EXE
            if getattr(sys, 'frozen', False):
                abs_path = resource_path(path)
            else:
                abs_path = path
                
            pixmap = QPixmap(abs_path)
            if not pixmap.isNull():
                # Масштабируем изображение, если оно слишком большое
                if pixmap.width() > max_width or pixmap.height() > max_height:
                    # Сохраняем пропорции
                    scaled = pixmap.scaled(
                        int(max_width), 
                        int(max_height), 
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.animation_frames.append(scaled)
                else:
                    self.animation_frames.append(pixmap)
        
        if self.animation_frames:
            self.current_frame_index = 0
            self.setPixmap(self.animation_frames[0])
            self.animation_timer.start(self.animation_speed)
            self.animation_loaded = True

    def load_gif_animation(self, gif_path, max_width, max_height):
        """Загружает GIF-анимацию"""
        if getattr(sys, 'frozen', False):
            abs_path = resource_path(gif_path)
        else:
            abs_path = gif_path
            
        # Создаем QMovie для GIF
        self.current_movie = QMovie(abs_path)
        
        if self.current_movie.isValid():
            # Получаем первый кадр для установки размера
            self.current_movie.jumpToFrame(0)
            pixmap = self.current_movie.currentPixmap()
            
            # Масштабируем при необходимости
            if pixmap.width() > max_width or pixmap.height() > max_height:
                scaled_size = pixmap.scaled(
                    int(max_width), 
                    int(max_height), 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ).size()
                self.current_movie.setScaledSize(scaled_size)
            
            # Устанавливаем базовую скорость для расчета
            self.base_gif_speed = 100  # 100 мс как база
            
            # Устанавливаем скорость
            self.set_gif_speed(self.animation_speed)
            
            # Подключаем сигналы
            self.current_movie.frameChanged.connect(self.update_gif_frame)
            self.setMovie(self.current_movie)
            self.current_movie.start()
            self.animation_loaded = True

    def update_gif_frame(self, frame_number):
        """Обновляет кадр для GIF-анимации"""
        if self.current_movie:
            self.setPixmap(self.current_movie.currentPixmap())

    def next_frame(self):
        """Обрабатывает следующий кадр для PNG-последовательности"""
        if not self.animation_frames or not self.animation_loaded:
            return
            
        self.current_frame_index = (self.current_frame_index + 1) % len(self.animation_frames)
        self.setPixmap(self.animation_frames[self.current_frame_index])

    def set_gif_speed(self, speed):
        """Устанавливает скорость для GIF на основе базовой скорости"""
        if self.current_movie:
            # Рассчитываем множитель скорости
            speed_factor = self.base_gif_speed / speed
            
            # Устанавливаем новую скорость
            self.current_movie.setSpeed(int(100 * speed_factor))

    def set_speed(self, speed):
        """Устанавливает скорость анимации (в мс)"""
        self.animation_speed = speed
        
        if self.animation_loaded:
            if self.current_movie:
                # Для GIF
                self.set_gif_speed(speed)
            else:
                # Для PNG-последовательности
                if self.animation_timer.isActive():
                    self.animation_timer.stop()
                self.animation_timer.start(speed)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition()

    def mouseMoveEvent(self, event):
        if self.oldPos:
            delta = event.globalPosition() - self.oldPos
            self.move(self.x() + int(delta.x()), self.y() + int(delta.y()))
            self.oldPos = event.globalPosition()

class AnimationTrayIcon(QSystemTrayIcon):
    def __init__(self, widget, parent=None):
        super().__init__(parent)
        self.widget = widget
        self.set_icon()  # Используем измененный метод
        
        menu = QMenu()
        
        # Меню загрузки анимации
        self.load_action = QAction("Загрузить анимацию...", self)
        self.load_action.triggered.connect(self.load_animation)
        menu.addAction(self.load_action)
        
        # Меню прозрачности
        self.opacity_menu = menu.addMenu("Прозрачность")
        self.setup_opacity_menu()
            
        # Меню скорости анимации
        self.speed_menu = menu.addMenu("Скорость анимации")
        self.setup_speed_menu()
        
        # Меню управления анимацией
        self.animation_menu = menu.addMenu("Управление анимацией")
        self.setup_animation_menu()
            
        # Выход
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.cleanup_and_exit)
        menu.addAction(exit_action)
        
        self.setContextMenu(menu)
    
    def set_icon(self):
        """Всегда создаем иконку программно для совместимости с EXE"""
        # Попробуем загрузить из файла
        try:
            icon_path = resource_path("icon.png")
            if os.path.exists(icon_path):
                self.setIcon(QIcon(icon_path))
                return
        except:
            pass
        
        # Если не получилось - создаем программно
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QBrush(Qt.GlobalColor.darkCyan))
        painter.drawEllipse(0, 0, 15, 15)
        painter.end()
        self.setIcon(QIcon(pixmap))

    def setup_opacity_menu(self):
        """Настраивает меню прозрачности"""
        self.opacity_menu.clear()
        for value in [100, 85, 70, 55, 40]:
            action = QAction(f"{value}%", self)
            action.triggered.connect(lambda checked, v=value: self.set_opacity(v))
            self.opacity_menu.addAction(action)
    
    def setup_speed_menu(self):
        """Настраивает меню скорости"""
        self.speed_menu.clear()
        speeds = [
            ("Очень медленно", 500),
            ("Медленно", 250),
            ("Средняя", 100),
            ("Быстро", 50),
            ("Очень быстро", 20)
        ]
        for text, speed in speeds:
            action = QAction(text, self)
            action.triggered.connect(lambda checked, s=speed: self.set_speed(s))
            self.speed_menu.addAction(action)
    
    def setup_animation_menu(self):
        """Настраивает меню управления анимацией"""
        self.animation_menu.clear()
        
        # Действие для паузы/возобновления
        self.pause_action = QAction("Пауза", self)
        self.pause_action.triggered.connect(self.toggle_pause)
        self.animation_menu.addAction(self.pause_action)
        
        # Действие для сброса позиции
        reset_action = QAction("Сбросить позицию", self)
        reset_action.triggered.connect(self.reset_position)
        self.animation_menu.addAction(reset_action)
    
    def set_opacity(self, value):
        self.widget.setWindowOpacity(value / 100)
    
    def set_speed(self, speed):
        self.widget.set_speed(speed)
    
    def load_animation(self):
        """Открывает диалог выбора файлов и загружает анимацию"""
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.png *.gif)")  # Добавили поддержку GIF
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            # Для GIF сортировка не нужна, для PNG - сортируем
            if len(file_paths) > 1 or not file_paths[0].lower().endswith('.gif'):
                file_paths.sort(key=lambda x: os.path.basename(x).lower())
            self.widget.load_animation(file_paths)
    
    def toggle_pause(self):
        """Приостанавливает или возобновляет анимацию"""
        if self.widget.current_movie:
            # Обработка для GIF
            if self.widget.current_movie.state() == QMovie.MovieState.Running:
                self.widget.current_movie.setPaused(True)
                self.pause_action.setText("Возобновить")
            else:
                self.widget.current_movie.setPaused(False)
                self.pause_action.setText("Пауза")
        else:
            # Обработка для PNG
            if self.widget.animation_timer.isActive():
                self.widget.animation_timer.stop()
                self.pause_action.setText("Возобновить")
            else:
                if self.widget.animation_loaded:
                    self.widget.animation_timer.start(self.widget.animation_speed)
                    self.pause_action.setText("Пауза")
    
    def reset_position(self):
        """Сбрасывает позицию анимации в центр экрана"""
        screen_geo = QApplication.primaryScreen().availableGeometry()
        new_x = (screen_geo.width() - self.widget.width()) // 2
        new_y = (screen_geo.height() - self.widget.height()) // 2
        self.widget.move(new_x, new_y)
    
    def cleanup_and_exit(self):
        """Корректно завершает работу приложения"""
        if self.widget.animation_timer.isActive():
            self.widget.animation_timer.stop()
        if self.widget.current_movie:
            self.widget.current_movie.stop()
        QApplication.quit()

class DummyWindow(QWidget):
    """Невидимое окно-заглушка, чтобы приложение не закрывалось"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Tool)
        self.resize(1, 1)
        self.move(-100, -100)  # Помещаем за пределы экрана

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Создаем виджет анимации
    widget = AnimationWidget()
    widget.setWindowOpacity(0.85)  # начальная прозрачность
    
    # Позиционируем по центру экрана
    screen_geo = QApplication.primaryScreen().availableGeometry()
    widget.resize(200, 200)  # начальный размер
    widget.move((screen_geo.width() - widget.width()) // 2, 
                (screen_geo.height() - widget.height()) // 2)
    widget.show()
    
    # Создаем невидимое окно-заглушку
    dummy_window = DummyWindow()
    dummy_window.show()
    
    # Создаем иконку в трее
    tray_icon = AnimationTrayIcon(widget)
    tray_icon.show()
    
    sys.exit(app.exec())