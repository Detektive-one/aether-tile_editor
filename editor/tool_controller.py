
from tools.paint_tool import PaintTool
from tools.erase_tool import EraseTool
from tools.fill_tool import FillTool
from tools.picker_tool import PickerTool

class ToolController:
    """Dispatches events to active tool"""
    
    def __init__(self, editor_state):
        self.editor_state = editor_state
        
        # Register all tools
        self.tools = {
            'paint': PaintTool(editor_state),
            'erase': EraseTool(editor_state),
            'fill': FillTool(editor_state),
            'picker': PickerTool(editor_state),
        }
        
        self.active_tool = self.tools['paint']
    
    def set_active_tool(self, tool_name: str):
        """Switch active tool"""
        if tool_name in self.tools:
            self.active_tool = self.tools[tool_name]
            self.editor_state.set_tool(tool_name)
    
    def get_active_tool(self):
        """Get current active tool"""
        return self.active_tool
    
    def on_mouse_down(self, grid_x: int, grid_y: int, button: int):
        self.active_tool.on_mouse_down(grid_x, grid_y, button)
    
    def on_mouse_move(self, grid_x: int, grid_y: int):
        self.editor_state.mouse_grid_x = grid_x
        self.editor_state.mouse_grid_y = grid_y
        self.active_tool.on_mouse_move(grid_x, grid_y)
    
    def on_mouse_up(self, grid_x: int, grid_y: int, button: int):
        self.active_tool.on_mouse_up(grid_x, grid_y, button)
