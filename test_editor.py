"""
MINIMAL WORKING TILE EDITOR - test_editor.py
This is a simplified standalone version to test if basic painting works
Run this file directly: python test_editor.py
"""
import sys
import pygame
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QImage
import numpy as np

class MinimalTileEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal Tile Editor - Test")
        self.resize(900, 700)
        
        # Initialize Pygame
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.HIDDEN)
        
        # Data
        self.tileset_image = None
        self.tile_size = 32
        self.tiles = []  # List of tile surfaces
        self.selected_tile = None
        
        # Map data (20x20 grid)
        self.map_width = 20
        self.map_height = 20
        self.map_data = np.zeros((self.map_height, self.map_width), dtype=int)
        
        # Canvas
        self.canvas_width = 640
        self.canvas_height = 640
        self.surface = pygame.Surface((self.canvas_width, self.canvas_height))
        
        # Mouse state
        self.painting = False
        
        # Setup UI
        self.setup_ui()
        
        # Render timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.render)
        self.timer.start(16)  # 60 FPS
        
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Info label
        self.info_label = QLabel("Click 'Import Tileset' to start")
        layout.addWidget(self.info_label)
        
        # Import button
        btn_import = QPushButton("Import Tileset (PNG)")
        btn_import.clicked.connect(self.import_tileset)
        layout.addWidget(btn_import)
        
        # Canvas widget
        self.canvas_widget = CanvasWidget(self.canvas_width, self.canvas_height)
        self.canvas_widget.mouse_pressed.connect(self.on_mouse_down)
        self.canvas_widget.mouse_moved.connect(self.on_mouse_move)
        self.canvas_widget.mouse_released.connect(self.on_mouse_up)
        layout.addWidget(self.canvas_widget)
        
        # Tile selector (simple)
        self.tile_label = QLabel("No tile selected")
        layout.addWidget(self.tile_label)
        
    def import_tileset(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Import Tileset", "", "Images (*.png *.jpg)")
        if not filename:
            return
        
        try:
            # Load image
            self.tileset_image = pygame.image.load(filename).convert_alpha()
            
            # Auto-detect tile size
            img_w, img_h = self.tileset_image.get_size()
            for size in [8, 16, 32, 64]:
                if img_w % size == 0 and img_h % size == 0:
                    self.tile_size = size
                    break
            
            # Slice into tiles
            self.tiles = []
            cols = img_w // self.tile_size
            rows = img_h // self.tile_size
            
            for row in range(rows):
                for col in range(cols):
                    rect = pygame.Rect(col * self.tile_size, row * self.tile_size, 
                                      self.tile_size, self.tile_size)
                    tile_surf = self.tileset_image.subsurface(rect)
                    self.tiles.append(tile_surf)
            
            # Select first tile
            if self.tiles:
                self.selected_tile = 0
                self.tile_label.setText(f"Tileset loaded! {len(self.tiles)} tiles. Selected: Tile 0 (Click to select tile 1)")
                self.info_label.setText(f"Loaded {cols}x{rows} tileset ({self.tile_size}x{self.tile_size}). LEFT CLICK to paint, RIGHT CLICK to select next tile")
            
        except Exception as e:
            self.info_label.setText(f"Error: {e}")
    
    def on_mouse_down(self, x, y, button):
        if button == 1:  # Left click - paint
            self.painting = True
            self.paint_tile(x, y)
        elif button == 3:  # Right click - cycle tile
            if self.tiles:
                self.selected_tile = (self.selected_tile + 1) % len(self.tiles)
                self.tile_label.setText(f"Selected tile: {self.selected_tile}")
    
    def on_mouse_move(self, x, y):
        if self.painting:
            self.paint_tile(x, y)
    
    def on_mouse_up(self, x, y, button):
        if button == 1:
            self.painting = False
    
    def paint_tile(self, screen_x, screen_y):
        if self.selected_tile is None or not self.tiles:
            return
        
        # Convert screen to grid
        grid_x = screen_x // self.tile_size
        grid_y = screen_y // self.tile_size
        
        # Bounds check
        if 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height:
            self.map_data[grid_y, grid_x] = self.selected_tile + 1  # +1 because 0 = empty
            self.info_label.setText(f"Painted tile {self.selected_tile} at ({grid_x}, {grid_y})")
    
    def render(self):
        # Clear
        self.surface.fill((50, 50, 50))
        
        # Draw grid
        for x in range(0, self.canvas_width, self.tile_size):
            pygame.draw.line(self.surface, (80, 80, 80), (x, 0), (x, self.canvas_height))
        for y in range(0, self.canvas_height, self.tile_size):
            pygame.draw.line(self.surface, (80, 80, 80), (0, y), (self.canvas_width, y))
        
        # Draw tiles
        if self.tiles:
            for y in range(self.map_height):
                for x in range(self.map_width):
                    tile_id = self.map_data[y, x]
                    if tile_id > 0 and tile_id <= len(self.tiles):
                        tile_surf = self.tiles[tile_id - 1]
                        self.surface.blit(tile_surf, (x * self.tile_size, y * self.tile_size))
        
        # Update Qt display
        self.canvas_widget.set_surface(self.surface)
        self.canvas_widget.update()


class CanvasWidget(QWidget):
    from PySide6.QtCore import Signal
    mouse_pressed = Signal(int, int, int)
    mouse_moved = Signal(int, int)
    mouse_released = Signal(int, int, int)
    
    def __init__(self, width, height):
        super().__init__()
        self.setFixedSize(width, height)
        self.surface = None
        self.qimage = None
        self.setMouseTracking(True)
    
    def set_surface(self, surface):
        self.surface = surface
        w, h = surface.get_size()
        data = pygame.image.tostring(surface, 'RGB')
        self.qimage = QImage(data, w, h, w * 3, QImage.Format_RGB888)
    
    def paintEvent(self, event):
        if self.qimage:
            painter = QPainter(self)
            painter.drawImage(0, 0, self.qimage)
    
    def mousePressEvent(self, event):
        button = 1 if event.button() == Qt.LeftButton else 3
        self.mouse_pressed.emit(event.pos().x(), event.pos().y(), button)
    
    def mouseMoveEvent(self, event):
        self.mouse_moved.emit(event.pos().x(), event.pos().y())
    
    def mouseReleaseEvent(self, event):
        button = 1 if event.button() == Qt.LeftButton else 3
        self.mouse_released.emit(event.pos().x(), event.pos().y(), button)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MinimalTileEditor()
    window.show()
    sys.exit(app.exec())
