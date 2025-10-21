import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional
from enum import Enum
import pygame
import os

class LayerType(Enum):
    # \"\"\"Types of layers available\"\"\"
    BACKGROUND = "background"
    PARALLAX = "parallax"
    ENVIRONMENT = "environment"
    ACTUAL = "actual"  # Main gameplay layer
    COLLISION = "collision"
    FOREGROUND = "foreground"
    PARTICLE = "particle"
    UI = "ui"
    CUSTOM = "custom"

@dataclass
class TileData:
    # \"\"\"Represents a single tile in the tileset\"\"\"
    id: int
    texture_rect: pygame.Rect
    solid: bool = False
    animation_frames: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'rect': [self.texture_rect.x, self.texture_rect.y, 
                    self.texture_rect.width, self.texture_rect.height],
            'solid': self.solid,
            'animation_frames': self.animation_frames,
            'metadata': self.metadata
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TileData':
        rect = pygame.Rect(*data['rect'])
        return TileData(
            id=data['id'],
            texture_rect=rect,
            solid=data.get('solid', False),
            animation_frames=data.get('animation_frames', []),
            metadata=data.get('metadata', {})
        )

class TileSet:
    # \"\"\"Collection of tiles from a spritesheet\"\"\"
    
    def __init__(self, name: str, image_path: str, tile_width: int = None, tile_height: int = None):
        self.name = name
        self.image_path = image_path
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.image: Optional[pygame.Surface] = None
        self.tiles: Dict[int, TileData] = {}
        
        # Load image
        if image_path and os.path.exists(image_path):
            self.load_image()
    
    def load_image(self):
        # \"\"\"Load the tileset image\"\"\"
        self.image = pygame.image.load(self.image_path).convert_alpha()
        
        # Auto-detect tile size if not provided
        if self.tile_width is None or self.tile_height is None:
            self._auto_detect_tile_size()
    
    def _auto_detect_tile_size(self):
        # \"\"\"Auto-detect common tile sizes (8x8, 16x16, 32x32, 64x64)\"\"\"
        
        img_w, img_h = self.image.get_size()
        
        # Common tile sizes
        common_sizes = [8, 16, 32, 64, 128]
        
        # Find the largest size that divides evenly
        for size in reversed(common_sizes):
            if img_w % size == 0 and img_h % size == 0:
                self.tile_width = size
                self.tile_height = size
                return
        
        # Default to 32x32 if no match
        self.tile_width = 32
        self.tile_height = 32
    
    def slice_from_image(self):
        # \"\"\"Auto-generate tiles by slicing the spritesheet\"\"\"
        if not self.image:
            return
            
        cols = self.image.get_width() // self.tile_width
        rows = self.image.get_height() // self.tile_height
        
        tile_id = 1  # ID 0 reserved for empty
        for row in range(rows):
            for col in range(cols):
                rect = pygame.Rect(
                    col * self.tile_width,
                    row * self.tile_height,
                    self.tile_width,
                    self.tile_height
                )
                self.tiles[tile_id] = TileData(id=tile_id, texture_rect=rect)
                tile_id += 1
    
    def get_tile_surface(self, tile_id: int) -> Optional[pygame.Surface]:
        # \"\"\"Extract a tile surface from the spritesheet\"\"\"
        if tile_id not in self.tiles or not self.image:
            return None
        tile = self.tiles[tile_id]
        return self.image.subsurface(tile.texture_rect)

class Layer:
    # \"\"\"Single editable layer with tile grid\"\"\"
    
    def __init__(self, name: str, width: int, height: int, layer_type: LayerType = LayerType.ACTUAL):
        self.name = name
        self.width = width
        self.height = height
        self.layer_type = layer_type
        self.tile_grid = np.zeros((height, width), dtype=np.int32)
        self.visible = True
        self.locked = False
        self.opacity = 1.0
        self.z_index = 0
        self.interacts_with_layers = True  # Can interact with other layers
        
    def get_tile(self, x: int, y: int) -> int:
            # \"\"\"Get tile ID at position\"\"\"
        if 0 <= x < self.width and 0 <= y < self.height:
            return int(self.tile_grid[y, x])
        return 0
    
    def set_tile(self, x: int, y: int, tile_id: int):
        # \"\"\"Set tile ID at position\"\"\"
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tile_grid[y, x] = tile_id
    
    def clear(self):
        # \"\"\"Clear all tiles from layer\"\"\"
        self.tile_grid.fill(0)

class MapProject:
    # \"\"\"Container for entire map project\"\"\"
    
    def __init__(self, name: str, grid_width: int, grid_height: int, 
                 tile_width: int, tile_height: int):
        self.name = name
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.layers: List[Layer] = []
        self.tileset: Optional[TileSet] = None
        self.metadata: Dict[str, Any] = {}
        self.project_path: Optional[str] = None
    
    def add_layer(self, name: str, layer_type: LayerType = LayerType.ACTUAL) -> Layer:
        # \"\"\"Create and add a new layer\"\"\"
        layer = Layer(name, self.grid_width, self.grid_height, layer_type)
        layer.z_index = len(self.layers)
        self.layers.append(layer)
        return layer
    
    def remove_layer(self, layer: Layer):
        # \"\"\"Remove a layer\"\"\"
        if layer in self.layers:
            self.layers.remove(layer)
            # Reindex remaining layers
            for i, l in enumerate(self.layers):
                l.z_index = i
    
    def get_layer_by_name(self, name: str) -> Optional[Layer]:
        # \"\"\"Find layer by name\"\"\"
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None