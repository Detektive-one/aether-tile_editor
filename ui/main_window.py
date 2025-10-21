
from PySide6.QtWidgets import (QMainWindow, QDockWidget, QToolBar, QFileDialog,
                               QMessageBox, QInputDialog, QWidget, QVBoxLayout,
                               QLabel, QStatusBar, QMenuBar)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QKeySequence
import pygame
import os

from .editor_canvas import EditorCanvas
from .tile_palette import TilePaletteWidget
from .layer_panel import LayerPanelWidget
from core.models import MapProject, TileSet, LayerType
from core.constants import (APP_NAME, APP_VERSION, DEFAULT_GRID_WIDTH,
                            DEFAULT_GRID_HEIGHT, DEFAULT_TILE_SIZE)
from editor.editor_state import EditorState
from data_io.project_io import ProjectIO


class TileEditorMainWindow(QMainWindow):
    """Main window for Aether Tile Editor"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1280, 720)
        
        # Initialize Pygame
        pygame.init()
        
        # Editor state
        self.editor_state = EditorState()
        
        # Create default project
        self.project = MapProject(
            name="Untitled",
            grid_width=DEFAULT_GRID_WIDTH,
            grid_height=DEFAULT_GRID_HEIGHT,
            tile_width=DEFAULT_TILE_SIZE,
            tile_height=DEFAULT_TILE_SIZE
        )
        
        # Add default layers
        self.project.add_layer("Background", LayerType.BACKGROUND)
        self.project.add_layer("Ground", LayerType.ACTUAL)
        self.project.add_layer("Collision", LayerType.COLLISION)
        
        # Set active layer
        self.editor_state.current_layer = self.project.layers[1]  # Ground layer
        
        # Setup UI
        self._create_canvas()
        self._create_dock_widgets()
        self._create_toolbar()
        self._create_menubar()
        self._create_statusbar()
        
        # Load settings
        self.settings = QSettings('Aether', 'TileEditor')
        self._load_settings()
    
    def _create_canvas(self):
        """Create main canvas"""
        self.canvas = EditorCanvas(
            self.project,
            self.editor_state,
            width=800,
            height=600
        )
        self.setCentralWidget(self.canvas)
    
    def _create_dock_widgets(self):
        """Create dockable panels"""
        # Tile palette
        tile_dock = QDockWidget("Tile Palette", self)
        tile_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.tile_palette = TilePaletteWidget()
        self.tile_palette.tile_selected.connect(self._on_tile_selected)
        tile_dock.setWidget(self.tile_palette)
        self.addDockWidget(Qt.RightDockWidgetArea, tile_dock)
        
        # Layer panel
        layer_dock = QDockWidget("Layers", self)
        layer_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.layer_panel = LayerPanelWidget(self.project)
        self.layer_panel.layer_selected.connect(self._on_layer_selected)
        self.layer_panel.layers_changed.connect(self._on_layers_changed)
        layer_dock.setWidget(self.layer_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, layer_dock)
    
    def _create_toolbar(self):
        """Create toolbar"""
        toolbar = QToolBar("Tools")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Paint tool
        action_paint = QAction("🖌 Paint", self)
        action_paint.setShortcut('P')
        action_paint.triggered.connect(lambda: self._set_tool('paint'))
        toolbar.addAction(action_paint)
        
        # Erase tool
        action_erase = QAction("🧹 Erase", self)
        action_erase.setShortcut('E')
        action_erase.triggered.connect(lambda: self._set_tool('erase'))
        toolbar.addAction(action_erase)
        
        # Fill tool
        action_fill = QAction("🪣 Fill", self)
        action_fill.setShortcut('F')
        action_fill.triggered.connect(lambda: self._set_tool('fill'))
        toolbar.addAction(action_fill)
        
        # Picker tool
        action_picker = QAction("💧 Picker", self)
        action_picker.setShortcut('I')
        action_picker.triggered.connect(lambda: self._set_tool('picker'))
        toolbar.addAction(action_picker)
        
        toolbar.addSeparator()
        
        # Grid toggle
        action_grid = QAction("📐 Grid", self)
        action_grid.setShortcut('G')
        action_grid.setCheckable(True)
        action_grid.setChecked(True)
        action_grid.triggered.connect(self._toggle_grid)
        toolbar.addAction(action_grid)
    
    def _create_menubar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        action_new = QAction("&New Project", self)
        action_new.setShortcut(QKeySequence.New)
        action_new.triggered.connect(self._new_project)
        file_menu.addAction(action_new)
        
        action_open = QAction("&Open Project...", self)
        action_open.setShortcut(QKeySequence.Open)
        action_open.triggered.connect(self._open_project)
        file_menu.addAction(action_open)
        
        file_menu.addSeparator()
        
        action_save = QAction("&Save Project", self)
        action_save.setShortcut(QKeySequence.Save)
        action_save.triggered.connect(self._save_project)
        file_menu.addAction(action_save)
        
        action_save_as = QAction("Save Project &As...", self)
        action_save_as.setShortcut(QKeySequence.SaveAs)
        action_save_as.triggered.connect(self._save_project_as)
        file_menu.addAction(action_save_as)
        
        file_menu.addSeparator()
        
        action_import_tileset = QAction("&Import Tileset...", self)
        action_import_tileset.setShortcut('Ctrl+I')
        action_import_tileset.triggered.connect(self._import_tileset)
        file_menu.addAction(action_import_tileset)
        
        file_menu.addSeparator()
        
        action_export_hdf5 = QAction("&Export to HDF5...", self)
        action_export_hdf5.triggered.connect(self._export_hdf5)
        file_menu.addAction(action_export_hdf5)
        
        file_menu.addSeparator()
        
        action_exit = QAction("E&xit", self)
        action_exit.setShortcut(QKeySequence.Quit)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        action_zoom_in = QAction("Zoom &In", self)
        action_zoom_in.setShortcut(QKeySequence.ZoomIn)
        action_zoom_in.triggered.connect(self.canvas.on_zoom_in)
        view_menu.addAction(action_zoom_in)
        
        action_zoom_out = QAction("Zoom &Out", self)
        action_zoom_out.setShortcut(QKeySequence.ZoomOut)
        action_zoom_out.triggered.connect(self.canvas.on_zoom_out)
        view_menu.addAction(action_zoom_out)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        action_about = QAction("&About", self)
        action_about.triggered.connect(self._show_about)
        help_menu.addAction(action_about)
    
    def _create_statusbar(self):
        """Create status bar"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")
    
    def _set_tool(self, tool_name: str):
        """Change active tool"""
        self.canvas.set_tool(tool_name)
        self.statusbar.showMessage(f"Tool: {tool_name.capitalize()}")
    
    def _toggle_grid(self):
        """Toggle grid visibility"""
        self.editor_state.grid_visible = not self.editor_state.grid_visible
        self.statusbar.showMessage(f"Grid: {'ON' if self.editor_state.grid_visible else 'OFF'}")
    
    def _on_tile_selected(self, tile_id: int):
        """Handle tile selection from palette"""
        self.editor_state.select_tile(tile_id)
        self.statusbar.showMessage(f"Selected tile: {tile_id}")
    
    def _on_layer_selected(self, layer):
        """Handle layer selection"""
        self.editor_state.set_active_layer(layer)
        self.statusbar.showMessage(f"Active layer: {layer.name}")
    
    def _on_layers_changed(self):
        """Handle layer changes"""
        self.layer_panel.refresh()
    
    def _new_project(self):
        """Create new project"""
        # Get project parameters
        name, ok = QInputDialog.getText(self, "New Project", "Project name:")
        if not ok or not name:
            return
        
        # Create new project
        self.project = MapProject(
            name=name,
            grid_width=DEFAULT_GRID_WIDTH,
            grid_height=DEFAULT_GRID_HEIGHT,
            tile_width=DEFAULT_TILE_SIZE,
            tile_height=DEFAULT_TILE_SIZE
        )
        
        # Add default layers
        self.project.add_layer("Background", LayerType.BACKGROUND)
        self.project.add_layer("Ground", LayerType.ACTUAL)
        
        # Update UI
        self.editor_state.current_layer = self.project.layers[0]
        self.canvas.project = self.project
        self.layer_panel.project = self.project
        self.layer_panel.refresh()
        
        self.setWindowTitle(f"{APP_NAME} - {name}")
        self.statusbar.showMessage("New project created")
    
    def _open_project(self):
        """Open existing project"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Open Project",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if not directory:
            return
        
        try:
            self.project = ProjectIO.load_project(directory)
            
            # Update UI
            if self.project.layers:
                self.editor_state.current_layer = self.project.layers[0]
            
            self.canvas.project = self.project
            self.layer_panel.project = self.project
            self.layer_panel.refresh()
            
            # Update tileset palette
            if self.project.tileset:
                self.tile_palette.set_tileset(self.project.tileset)
            
            self.setWindowTitle(f"{APP_NAME} - {self.project.name}")
            self.statusbar.showMessage(f"Opened: {directory}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open project:\\n{str(e)}")
    
    def _save_project(self):
        """Save current project"""
        if self.project.project_path:
            try:
                ProjectIO.save_project(self.project, self.project.project_path)
                self.statusbar.showMessage(f"Saved: {self.project.project_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\\n{str(e)}")
        else:
            self._save_project_as()
    
    def _save_project_as(self):
        """Save project to new location"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Save Project As",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if not directory:
            return
        
        try:
            ProjectIO.save_project(self.project, directory)
            self.statusbar.showMessage(f"Saved: {directory}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\\n{str(e)}")
    
    def _import_tileset(self):
        """Import tileset image"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Tileset",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if not filename:
            return
        
        try:
            # Create tileset
            tileset_name = os.path.splitext(os.path.basename(filename))[0]
            tileset = TileSet(tileset_name, filename)
            
            # Auto-detect tile size and slice
            tileset.slice_from_image()
            
            self.project.tileset = tileset
            
            # Update tile palette
            self.tile_palette.set_tileset(tileset)
            
            # Update canvas tile size if needed
            if self.project.tile_width != tileset.tile_width:
                self.project.tile_width = tileset.tile_width
                self.project.tile_height = tileset.tile_height
            
            self.statusbar.showMessage(
                f"Imported tileset: {tileset_name} " +
                f"({tileset.tile_width}x{tileset.tile_height}, {len(tileset.tiles)} tiles)"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import tileset:\\n{str(e)}")
    
    def _export_hdf5(self):
        """Export project to HDF5"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to HDF5",
            f"{self.project.name}.h5",
            "HDF5 Files (*.h5 *.hdf5)"
        )
        
        if not filename:
            return
        
        try:
            ProjectIO.export_to_hdf5(self.project, filename)
            QMessageBox.information(self, "Success", f"Exported to:\\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export:\\n{str(e)}")
    
    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"""<h2>{APP_NAME}</h2>
            <p>Version {APP_VERSION}</p>
            <p>A professional tile editor for the Aether game framework.</p>
            <p><b>Features:</b></p>
            <ul>
            <li>Multi-layer tile editing</li>
            <li>Auto-detect tile sizes (8x8, 16x16, 32x32, etc.)</li>
            <li>Binary layer format with HDF5 export</li>
            <li>Paint, erase, fill, and picker tools</li>
            <li>Layer types: background, parallax, collision, etc.</li>
            </ul>
            <p>© 2025 Aether Framework</p>
            """
        )
    
    def _load_settings(self):
        """Load application settings"""
        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self.settings.value('windowState')
        if state:
            self.restoreState(state)
    
    def _save_settings(self):
        """Save application settings"""
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
    
    def closeEvent(self, event):
        """Handle window close"""
        self._save_settings()
        event.accept()
