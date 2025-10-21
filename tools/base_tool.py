
from abc import ABC, abstractmethod

class BaseTool(ABC):
    # \"\"\"Abstract base class for all editing tools\"\"\"
    
    def __init__(self, editor_state):
        self.editor_state = editor_state
        self.is_active = False
    
    @abstractmethod
    def on_mouse_down(self, grid_x: int, grid_y: int, button: int):
        # \"\"\"Called when mouse button is pressed\"\"\"
        pass
    
    @abstractmethod
    def on_mouse_move(self, grid_x: int, grid_y: int):
        # \"\"\"Called when mouse is moved\"\"\"
        pass
    
    @abstractmethod
    def on_mouse_up(self, grid_x: int, grid_y: int, button: int):
        # \"\"\"Called when mouse button is released\"\"\"
        pass
    
    @abstractmethod
    def get_cursor_name(self) -> str:
        # \"\"\"Return cursor name for this tool\"\"\"
        pass

