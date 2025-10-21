class EditorState:
    """Manages global editor state"""
    
    def __init__(self):
        self.current_layer = None
        self.selected_tile_id = None
        self.current_tool = 'paint'
        self.grid_visible = True
        self.mouse_grid_x = 0
        self.mouse_grid_y = 0
    
    def get_active_layer(self):
        """Get currently active layer"""
        return self.current_layer
    
    def set_active_layer(self, layer):
        """Set active layer for editing"""
        if layer and not layer.locked:
            self.current_layer = layer
    
    def select_tile(self, tile_id: int):
        """Select tile from palette"""
        self.selected_tile_id = tile_id
    
    def set_tool(self, tool_name: str):
        """Set current tool"""
        self.current_tool = tool_name
