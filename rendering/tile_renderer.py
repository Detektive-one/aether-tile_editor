import pygame
from typing import Optional

class TileRenderer:
    # \"\"\"Renders tiles and layers to pygame surface\"\"\"
    
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        self.grid_visible = True
        
    def render_layer(self, layer, tileset, tile_width: int, tile_height: int):
        # \"\"\"Render a single layer\"\"\"
        if not layer.visible or tileset is None or tileset.image is None:
            return
        
        # Calculate visible tile range (viewport culling)
        screen_w, screen_h = self.surface.get_size()
        
        scaled_tile_w = int(tile_width * self.zoom)
        scaled_tile_h = int(tile_height * self.zoom)
        
        start_x = max(0, int(self.camera_x / scaled_tile_w))
        start_y = max(0, int(self.camera_y / scaled_tile_h))
        end_x = min(layer.width, int((self.camera_x + screen_w) / scaled_tile_w) + 2)
        end_y = min(layer.height, int((self.camera_y + screen_h) / scaled_tile_h) + 2)
        
        # Render visible tiles
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile_id = layer.get_tile(x, y)
                if tile_id == 0:
                    continue
                
                tile_surface = tileset.get_tile_surface(tile_id)
                if tile_surface is None:
                    continue
                
                # Calculate screen position
                screen_x = int(x * scaled_tile_w - self.camera_x)
                screen_y = int(y * scaled_tile_h - self.camera_y)
                
                # Scale if needed
                if self.zoom != 1.0:
                    tile_surface = pygame.transform.scale(
                        tile_surface,
                        (scaled_tile_w, scaled_tile_h)
                    )
                
                # Apply opacity
                if layer.opacity < 1.0:
                    tile_surface = tile_surface.copy()
                    tile_surface.set_alpha(int(255 * layer.opacity))
                
                self.surface.blit(tile_surface, (screen_x, screen_y))
    
    def draw_grid(self, layer_width: int, layer_height: int,
                  tile_width: int, tile_height: int):
        # \"\"\"Draw grid overlay\"\"\"
        if not self.grid_visible:
            return
        
        screen_w, screen_h = self.surface.get_size()
        scaled_tile_w = int(tile_width * self.zoom)
        scaled_tile_h = int(tile_height * self.zoom)
        
        # Only draw grid if tiles are large enough
        if scaled_tile_w < 4 or scaled_tile_h < 4:
            return
        
        # Vertical lines
        start_x = int(self.camera_x / scaled_tile_w)
        end_x = min(layer_width, int((self.camera_x + screen_w) / scaled_tile_w) + 2)
        
        for x in range(start_x, end_x + 1):
            screen_x = int(x * scaled_tile_w - self.camera_x)
            if 0 <= screen_x <= screen_w:
                pygame.draw.line(
                    self.surface,
                    (100, 100, 100),
                    (screen_x, 0),
                    (screen_x, screen_h)
                )
        
        # Horizontal lines
        start_y = int(self.camera_y / scaled_tile_h)
        end_y = min(layer_height, int((self.camera_y + screen_h) / scaled_tile_h) + 2)
        
        for y in range(start_y, end_y + 1):
            screen_y = int(y * scaled_tile_h - self.camera_y)
            if 0 <= screen_y <= screen_h:
                pygame.draw.line(
                    self.surface,
                    (100, 100, 100),
                    (0, screen_y),
                    (screen_w, screen_y)
                )
    
    def draw_selection_highlight(self, grid_x: int, grid_y: int,
                                   tile_width: int, tile_height: int):
        # \"\"\"Draw highlight around selected tile position\"\"\"
        scaled_tile_w = int(tile_width * self.zoom)
        scaled_tile_h = int(tile_height * self.zoom)
        
        screen_x = int(grid_x * scaled_tile_w - self.camera_x)
        screen_y = int(grid_y * scaled_tile_h - self.camera_y)
        
        # Draw yellow highlight rectangle
        rect = pygame.Rect(screen_x, screen_y, scaled_tile_w, scaled_tile_h)
        pygame.draw.rect(self.surface, (255, 255, 0), rect, 2)
    
    def screen_to_grid(self, screen_x: int, screen_y: int,
                       tile_width: int, tile_height: int) -> tuple:
        # \"\"\"Convert screen coordinates to grid coordinates\"\"\"
        scaled_tile_w = tile_width * self.zoom
        scaled_tile_h = tile_height * self.zoom
        
        grid_x = int((screen_x + self.camera_x) / scaled_tile_w)
        grid_y = int((screen_y + self.camera_y) / scaled_tile_h)
        
        return grid_x, grid_y
    
    def set_zoom(self, zoom: float):
        # \"\"\"Set zoom level with clamping\"\"\"
        from core.constants import ZOOM_MIN, ZOOM_MAX
        self.zoom = max(ZOOM_MIN, min(ZOOM_MAX, zoom))
    
    def pan(self, dx: int, dy: int):
        # \"\"\"Pan camera\"\"\"
        self.camera_x = max(0, self.camera_x + dx)
        self.camera_y = max(0, self.camera_y + dy)
