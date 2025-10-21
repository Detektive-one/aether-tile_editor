
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt, Signal, QPoint
from PySide6.QtGui import QPainter, QImage
import pygame
import os

class PygameCanvasWidget(QWidget):
    # \"\"\"Canvas widget that embeds Pygame rendering\"\"\"
    
    mouse_pressed = Signal(int, int, int)  # x, y, button
    mouse_moved = Signal(int, int)  # x, y
    mouse_released = Signal(int, int, int)  # x, y, button
    
    def __init__(self, width=800, height=600, parent=None):
        super().__init__(parent)
        self.canvas_width = width
        self.canvas_height = height
        
        # Set fixed size
        self.setMinimumSize(width, height)
        self.setFocusPolicy(Qt.StrongFocus)
        
        # Initialize Pygame
        os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Use dummy driver for offscreen
        pygame.init()
        
        # Create offscreen Pygame surface
        self.pygame_surface = pygame.Surface((width, height))
        
        # Rendering timer (60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_display)
        self.timer.start(16)  # ~60 FPS
        
        # Mouse tracking
        self.setMouseTracking(True)
        self.mouse_down = False
        self.last_mouse_pos = QPoint(0, 0)
        self.middle_mouse_down = False
    
    def update_display(self):
        # \"\"\"Update display (called by timer)\"\"\"
        # Trigger render
        self.render()
        
        # Trigger Qt repaint
        self.update()
    
    def render(self):
        # \"\"\"Override this to draw on pygame_surface\"\"\"
        self.pygame_surface.fill((50, 50, 50))
    
    def paintEvent(self, event):
        # \"\"\"Qt paint event - convert Pygame surface to Qt\"\"\"
        # Convert pygame surface to QImage
        w, h = self.pygame_surface.get_size()
        data = pygame.image.tostring(self.pygame_surface, 'RGB')
        qimage = QImage(data, w, h, w * 3, QImage.Format_RGB888)
        
        # Draw to widget
        painter = QPainter(self)
        painter.drawImage(0, 0, qimage)
    
    def mousePressEvent(self, event):
        # \"\"\"Handle mouse press\"\"\"
        if event.button() == Qt.LeftButton:
            self.mouse_down = True
            self.mouse_pressed.emit(event.pos().x(), event.pos().y(), 1)
        elif event.button() == Qt.RightButton:
            self.mouse_pressed.emit(event.pos().x(), event.pos().y(), 3)
        elif event.button() == Qt.MiddleButton:
            self.middle_mouse_down = True
            self.last_mouse_pos = event.pos()
    
    def mouseMoveEvent(self, event):
        # \"\"\"Handle mouse move\"\"\"
        self.mouse_moved.emit(event.pos().x(), event.pos().y())
        
        # Middle mouse pan
        if self.middle_mouse_down:
            dx = self.last_mouse_pos.x() - event.pos().x()
            dy = self.last_mouse_pos.y() - event.pos().y()
            self.on_pan(dx, dy)
            self.last_mouse_pos = event.pos()
    
    def mouseReleaseEvent(self, event):
        # \"\"\"Handle mouse release\"\"\"
        if event.button() == Qt.LeftButton:
            self.mouse_down = False
            self.mouse_released.emit(event.pos().x(), event.pos().y(), 1)
        elif event.button() == Qt.RightButton:
            self.mouse_released.emit(event.pos().x(), event.pos().y(), 3)
        elif event.button() == Qt.MiddleButton:
            self.middle_mouse_down = False
    
    def wheelEvent(self, event):
        # \"\"\"Handle mouse wheel for zoom\"\"\"
        delta = event.angleDelta().y()
        if delta > 0:
            self.on_zoom_in()
        else:
            self.on_zoom_out()
    
    def on_pan(self, dx, dy):
        # \"\"\"Override for pan handling\"\"\"
        pass
    
    def on_zoom_in(self):
        # \"\"\"Override for zoom in\"\"\"
        pass
    
    def on_zoom_out(self):
        # \"\"\"Override for zoom out\"\"\"
        pass
    
    def resizeEvent(self, event):
        # \"\"\"Handle resize\"\"\"
        new_size = event.size()
        self.canvas_width = new_size.width()
        self.canvas_height = new_size.height()
        
        # Resize pygame surface
        self.pygame_surface = pygame.Surface((self.canvas_width, self.canvas_height))
        
        super().resizeEvent(event)
