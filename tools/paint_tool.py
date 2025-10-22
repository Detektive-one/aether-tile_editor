from .base_tool import BaseTool

class PaintTool(BaseTool):
    # \"\"\"Tool for painting tiles on canvas\"\"\"
    
    def __init__(self, editor_state):
        super().__init__(editor_state)
        self.last_painted = None
    
    def on_mouse_down(self, grid_x: int, grid_y: int, button: int):
        if button == 1:  # Left click
            self._paint_tile(grid_x, grid_y)
            self.is_active = True
    
    def on_mouse_move(self, grid_x: int, grid_y: int):
        if self.is_active:
            # Avoid painting same tile twice
            if (grid_x, grid_y) != self.last_painted:
                self._paint_tile(grid_x, grid_y)
    
    def on_mouse_up(self, grid_x: int, grid_y: int, button: int):
        self.is_active = False
        self.last_painted = None
    
    def _paint_tile(self, grid_x: int, grid_y: int):
        """Paint selected tile at position"""
        layer = self.editor_state.current_layer
        tile_id = self.editor_state.selected_tile_id
        
        # ADD THESE DEBUG LINES:
        print(f"\n=== PAINT TOOL DEBUG ===")
        print(f"Grid position: ({grid_x}, {grid_y})")
        print(f"Layer: {layer}")
        print(f"Tile ID: {tile_id}")
        
        if layer and not layer.locked and tile_id is not None:
            if 0 <= grid_x < layer.width and 0 <= grid_y < layer.height:
                print(f"✓ PAINTING tile {tile_id} at ({grid_x}, {grid_y})")
                layer.set_tile(grid_x, grid_y, tile_id)
                self.last_painted = (grid_x, grid_y)
            else:
                print(f"✗ OUT OF BOUNDS: ({grid_x}, {grid_y}) not in 0-{layer.width}, 0-{layer.height}")
        else:
            print(f"✗ CANNOT PAINT:")
            print(f"  Layer exists: {layer is not None}")

            if layer:
                print(f"  Layer locked: {layer.locked}")
            print(f"  Tile selected: {tile_id is not None}")
        print("=======================\n")
    
    def get_cursor_name(self) -> str:
        return "paint"



