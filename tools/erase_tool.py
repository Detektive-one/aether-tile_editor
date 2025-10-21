from .base_tool import BaseTool

class EraseTool(BaseTool):
    # \"\"\"Tool for erasing tiles\"\"\"
    
    def __init__(self, editor_state):
        super().__init__(editor_state)
        self.last_erased = None
    
    def on_mouse_down(self, grid_x: int, grid_y: int, button: int):
        if button == 1:  # Left click
            self._erase_tile(grid_x, grid_y)
            self.is_active = True
    
    def on_mouse_move(self, grid_x: int, grid_y: int):
        if self.is_active:
            if (grid_x, grid_y) != self.last_erased:
                self._erase_tile(grid_x, grid_y)
    
    def on_mouse_up(self, grid_x: int, grid_y: int, button: int):
        self.is_active = False
        self.last_erased = None
    
    def _erase_tile(self, grid_x: int, grid_y: int):
        # \"\"\"Erase tile at position\"\"\"
        layer = self.editor_state.current_layer
        
        if layer and not layer.locked:
            if 0 <= grid_x < layer.width and 0 <= grid_y < layer.height:
                layer.set_tile(grid_x, grid_y, 0)
                self.last_erased = (grid_x, grid_y)
    
    def get_cursor_name(self) -> str:
        return "erase"

