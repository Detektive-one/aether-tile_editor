from .canvas_widget import PygameCanvasWidget
from rendering.tile_renderer import TileRenderer
from editor.tool_controller import ToolController
from core.constants import ZOOM_STEP

class EditorCanvas(PygameCanvasWidget):
    # \"\"\"Canvas for tile map editing\"\"\"
    
    def __init__(self, project, editor_state, width=800, height=600, parent=None):
        super().__init__(width, height, parent)
        
        self.project = project
        self.editor_state = editor_state
        self.renderer = TileRenderer(self.pygame_surface)
        self.tool_controller = ToolController(editor_state)
        
        # Connect signals
        self.mouse_pressed.connect(self.on_mouse_pressed)
        self.mouse_moved.connect(self.on_mouse_moved_internal)
        self.mouse_released.connect(self.on_mouse_released)
    
    def render(self):
        # \"\"\"Render the tilemap\"\"\"
        # Clear background
        self.pygame_surface.fill((40, 40, 40))
        
        if self.project.tileset is None:
            return
        
        # Render all visible layers (sorted by z_index)
        for layer in sorted(self.project.layers, key=lambda l: l.z_index):
            self.renderer.render_layer(
                layer,
                self.project.tileset,
                self.project.tile_width,
                self.project.tile_height
            )
        
        # Draw grid
        if self.editor_state.grid_visible:
            self.renderer.draw_grid(
                self.project.grid_width,
                self.project.grid_height,
                self.project.tile_width,
                self.project.tile_height
            )
        
        # Draw cursor highlight
        if self.editor_state.current_layer:
            self.renderer.draw_selection_highlight(
                self.editor_state.mouse_grid_x,
                self.editor_state.mouse_grid_y,
                self.project.tile_width,
                self.project.tile_height
            )
    
    def on_mouse_pressed(self, x, y, button):
        # \"\"\"Handle mouse press\"\"\"
        grid_x, grid_y = self.renderer.screen_to_grid(
            x, y,
            self.project.tile_width,
            self.project.tile_height
        )
        self.tool_controller.on_mouse_down(grid_x, grid_y, button)
    
    def on_mouse_moved_internal(self, x, y):
        # \"\"\"Handle mouse move\"\"\"
        grid_x, grid_y = self.renderer.screen_to_grid(
            x, y,
            self.project.tile_width,
            self.project.tile_height
        )
        self.tool_controller.on_mouse_move(grid_x, grid_y)
    
    def on_mouse_released(self, x, y, button):
        # \"\"\"Handle mouse release\"\"\"
        grid_x, grid_y = self.renderer.screen_to_grid(
            x, y,
            self.project.tile_width,
            self.project.tile_height
        )
        self.tool_controller.on_mouse_up(grid_x, grid_y, button)
    
    def on_pan(self, dx, dy):
        # \"\"\"Handle panning\"\"\"
        self.renderer.pan(dx, dy)
    
    def on_zoom_in(self):
        # \"\"\"Zoom in\"\"\"
        new_zoom = self.renderer.zoom + ZOOM_STEP
        self.renderer.set_zoom(new_zoom)
    
    def on_zoom_out(self):
        # \"\"\"Zoom out\"\"\"
        new_zoom = self.renderer.zoom - ZOOM_STEP
        self.renderer.set_zoom(new_zoom)
    
    def set_tool(self, tool_name: str):
        # \"\"\"Change active tool\"\"\"
        self.tool_controller.set_active_tool(tool_name)
