from .base_tool import BaseTool

class PickerTool(BaseTool):
    # \"\"\"Tool for picking tiles from canvas\"\"\"
    
    def on_mouse_down(self, grid_x: int, grid_y: int, button: int):
        if button == 1:  # Left click
            self._pick_tile(grid_x, grid_y)
    
    def on_mouse_move(self, grid_x: int, grid_y: int):
        pass
    
    def on_mouse_up(self, grid_x: int, grid_y: int, button: int):
        pass
    
    def _pick_tile(self, grid_x: int, grid_y: int):
        # \"\"\"Pick tile from current layer\"\"\"
        layer = self.editor_state.current_layer
        
        if layer:
            if 0 <= grid_x < layer.width and 0 <= grid_y < layer.height:
                tile_id = layer.get_tile(grid_x, grid_y)
                if tile_id > 0:
                    self.editor_state.selected_tile_id = tile_id
    
    def get_cursor_name(self) -> str:
        return "picker"