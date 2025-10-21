from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, 
                               QGridLayout, QLabel, QPushButton, QFrame)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QPainter, QPen, QImage
import pygame

class TilePaletteWidget(QWidget):
    # """Widget displaying tileset palette for selection"""
    
    tile_selected = Signal(int)  # tile_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tileset = None
        self.selected_tile_id = None
        self.tile_buttons = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        # """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container for tiles
        self.tiles_container = QWidget()
        self.tiles_layout = QGridLayout(self.tiles_container)
        self.tiles_layout.setSpacing(2)
        
        scroll.setWidget(self.tiles_container)
        layout.addWidget(scroll)
    
    def set_tileset(self, tileset):
        # """Load and display tileset"""
        self.tileset = tileset
        self.selected_tile_id = None
        self._populate_tiles()
    
    def _populate_tiles(self):
        # """Populate tile palette from tileset"""
        # Clear existing tiles
        for button in self.tile_buttons.values():
            button.deleteLater()
        self.tile_buttons.clear()
        
        if not self.tileset or not self.tileset.tiles:
            return
        
        # Calculate grid dimensions
        tiles_per_row = 4
        
        # Create tile buttons
        for tile_id, tile_data in sorted(self.tileset.tiles.items()):
            tile_surface = self.tileset.get_tile_surface(tile_id)
            if tile_surface is None:
                continue
            
            # Convert pygame surface to QPixmap
            w, h = tile_surface.get_size()
            data = pygame.image.tostring(tile_surface, 'RGBA')
            qimage = QImage(data, w, h, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)
            
            # Create button
            button = QPushButton()
            button.setIcon(pixmap)
            button.setIconSize(pixmap.size())
            button.setFixedSize(pixmap.width() + 10, pixmap.height() + 10)
            button.setStyleSheet("""
                QPushButton {
                    border: 2px solid #555;
                    background: #333;
                }
                QPushButton:hover {
                    border: 2px solid #888;
                }
                QPushButton:pressed {
                    border: 2px solid #ff0;
                }
            """)
            
            # Store tile_id
            button.setProperty('tile_id', tile_id)
            button.clicked.connect(lambda checked, tid=tile_id: self._on_tile_clicked(tid))
            
            # Add to grid
            row = (tile_id - 1) // tiles_per_row
            col = (tile_id - 1) % tiles_per_row
            self.tiles_layout.addWidget(button, row, col)
            
            self.tile_buttons[tile_id] = button
    
    def _on_tile_clicked(self, tile_id: int):
        # """Handle tile selection"""
        # Update selection
        self.selected_tile_id = tile_id
        
        # Update button styles
        for tid, button in self.tile_buttons.items():
            if tid == tile_id:
                button.setStyleSheet("""
                    QPushButton {
                        border: 3px solid #ff0;
                        background: #444;
                    }
                """)
            else:
                button.setStyleSheet("""
                    QPushButton {
                        border: 2px solid #555;
                        background: #333;
                    }
                    QPushButton:hover {
                        border: 2px solid #888;
                    }
                """)
        
        # Emit signal
        self.tile_selected.emit(tile_id)

