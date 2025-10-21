from .base_tool import BaseTool
from collections import deque

class FillTool(BaseTool):
    # \"\"\"Flood fill tool\"\"\"
    
    def on_mouse_down(self, grid_x: int, grid_y: int, button: int):
        if button == 1:  # Left click
            self._flood_fill(grid_x, grid_y)
    
    def on_mouse_move(self, grid_x: int, grid_y: int):
        pass  # No drag behavior
    
    def on_mouse_up(self, grid_x: int, grid_y: int, button: int):
        pass
    
    def _flood_fill(self, start_x: int, start_y: int):
        # \"\"\"Flood fill algorithm (BFS)\"\"\"
        layer = self.editor_state.current_layer
        new_tile = self.editor_state.selected_tile_id
        
        if layer is None or layer.locked or new_tile is None:
            return
        
        # Check bounds
        if not (0 <= start_x < layer.width and 0 <= start_y < layer.height):
            return
        
        target_tile = layer.get_tile(start_x, start_y)
        
        # Don't fill if same tile
        if target_tile == new_tile:
            return
        
        # BFS flood fill
        queue = deque([(start_x, start_y)])
        visited = set()
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) in visited:
                continue
            
            if not (0 <= x < layer.width and 0 <= y < layer.height):
                continue
            
            if layer.get_tile(x, y) != target_tile:
                continue
            
            visited.add((x, y))
            layer.set_tile(x, y, new_tile)
            
            # Add neighbors (4-directional)
            queue.append((x + 1, y))
            queue.append((x - 1, y))
            queue.append((x, y + 1))
            queue.append((x, y - 1))
    
    def get_cursor_name(self) -> str:
        return "fill"

