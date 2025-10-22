from PySide6.QtWidgets import (QMainWindow, QDockWidget, QToolBar, QFileDialog,
                               QMessageBox, QInputDialog, QWidget, QVBoxLayout,
                               QLabel, QStatusBar, QDialog, QComboBox, QLineEdit,
                               QPushButton, QHBoxLayout, QSpinBox, QFormLayout)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QKeySequence
import pygame
import os

from ui.editor_canvas import EditorCanvas
from ui.tile_palette import TilePaletteWidget
from ui.layer_panel import LayerPanelWidget
from core.models import MapProject, TileSet, LayerType
from core.constants import (APP_NAME, APP_VERSION, DEFAULT_GRID_WIDTH,
                            DEFAULT_GRID_HEIGHT, DEFAULT_TILE_SIZE)
from editor.editor_state import EditorState
from fileio.project_io import ProjectIO


class AddLayerDialog(QDialog):
    """Dialog for adding a new layer with type selection"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Layer")
        self.resize(350, 150)
        
        layout = QFormLayout(self)
        
        # Layer name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter layer name...")
        layout.addRow("Layer Name:", self.name_edit)
        
        # Layer type
        self.type_combo = QComboBox()
        for layer_type in LayerType:
            self.type_combo.addItem(layer_type.value.capitalize(), layer_type)
        layout.addRow("Layer Type:", self.type_combo)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        layout.addRow("", button_layout)
    
    def get_layer_data(self):
        """Return (name, layer_type)"""
        return self.name_edit.text(), self.type_combo.currentData()


class TileSubdivisionDialog(QDialog):
    """Dialog for manual tile size override"""
    
    def __init__(self, current_size, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tile Subdivision")
        self.resize(300, 120)
        
        layout = QFormLayout(self)
        
        layout.addRow(QLabel(f"Current tile size: {current_size}x{current_size}"))
        
        # New tile size
        self.tile_size_spin = QSpinBox()
        self.tile_size_spin.setMinimum(4)
        self.tile_size_spin.setMaximum(256)
        self.tile_size_spin.setValue(current_size)
        self.tile_size_spin.setSingleStep(4)
        layout.addRow("New Tile Size:", self.tile_size_spin)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.btn_ok = QPushButton("Apply")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        layout.addRow("", button_layout)
    
    def get_tile_size(self):
        """Return new tile size"""
        return self.tile_size_spin.value()


class TileEditorMainWindow(QMainWindow):
    """Main window for Aether Tile Editor"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1280, 720)
        
        # Initialize Pygame FIRST with a hidden display
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.HIDDEN)
        
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
        
        # Initialize grid as visible
        self.editor_state.grid_visible = True
        self.canvas.renderer.grid_visible = True
        
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
        self.action_paint = QAction("🖌 Paint", self)
        self.action_paint.setShortcut('P')
        self.action_paint.setCheckable(True)
        self.action_paint.setChecked(True)
        self.action_paint.triggered.connect(lambda: self._set_tool('paint'))
        toolbar.addAction(self.action_paint)
        
        # Erase tool
        self.action_erase = QAction("🧹 Erase", self)
        self.action_erase.setShortcut('E')
        self.action_erase.setCheckable(True)
        self.action_erase.triggered.connect(lambda: self._set_tool('erase'))
        toolbar.addAction(self.action_erase)
        
        # Fill tool
        self.action_fill = QAction("🪣 Fill", self)
        self.action_fill.setShortcut('F')
        self.action_fill.setCheckable(True)
        self.action_fill.triggered.connect(lambda: self._set_tool('fill'))
        toolbar.addAction(self.action_fill)
        
        # Picker tool
        self.action_picker = QAction("💧 Picker", self)
        self.action_picker.setShortcut('I')
        self.action_picker.setCheckable(True)
        self.action_picker.triggered.connect(lambda: self._set_tool('picker'))
        toolbar.addAction(self.action_picker)
        
        toolbar.addSeparator()
        
        # Grid toggle
        self.action_grid = QAction("📐 Grid", self)
        self.action_grid.setShortcut('G')
        self.action_grid.setCheckable(True)
        self.action_grid.setChecked(True)
        self.action_grid.triggered.connect(self._toggle_grid)
        toolbar.addAction(self.action_grid)
    
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
        
        action_subdivide = QAction("Subdivide &Tiles...", self)
        action_subdivide.setShortcut('Ctrl+T')
        action_subdivide.triggered.connect(self._subdivide_tiles)
        file_menu.addAction(action_subdivide)
        
        file_menu.addSeparator()
        
        action_export_hdf5 = QAction("Export to &HDF5...", self)
        action_export_hdf5.triggered.connect(self._export_hdf5)
        file_menu.addAction(action_export_hdf5)
        
        action_export_png = QAction("Export to &PNG...", self)
        action_export_png.triggered.connect(self._export_png)
        file_menu.addAction(action_export_png)
        
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
        self.statusbar.showMessage("Ready - Press 'P' to paint, 'E' to erase, 'F' to fill")
    
    def _set_tool(self, tool_name: str):
        """Change active tool"""
        # Uncheck all tool actions
        self.action_paint.setChecked(tool_name == 'paint')
        self.action_erase.setChecked(tool_name == 'erase')
        self.action_fill.setChecked(tool_name == 'fill')
        self.action_picker.setChecked(tool_name == 'picker')
        
        self.canvas.set_tool(tool_name)
        self.statusbar.showMessage(f"Tool: {tool_name.capitalize()}")
    
    def _toggle_grid(self):
        """Toggle grid visibility"""
        self.editor_state.grid_visible = self.action_grid.isChecked()
        self.canvas.renderer.grid_visible = self.editor_state.grid_visible
        self.statusbar.showMessage(f"Grid: {'ON' if self.editor_state.grid_visible else 'OFF'}")
    
    def _on_tile_selected(self, tile_id: int):
        """Handle tile selection from palette"""
        self.editor_state.select_tile(tile_id)
        self.statusbar.showMessage(f"Selected tile: {tile_id}")
    
    def _on_tile_selected(self, tile_id: int):
        self.editor_state.select_tile(tile_id)
        # ADD THESE DEBUG LINES:
        print(f"\n=== TILE SELECTED DEBUG ===")
        print(f"Tile ID: {tile_id}")
        print(f"Editor state tile: {self.editor_state.selected_tile_id}")
        print(f"Current layer: {self.editor_state.current_layer}")
        if self.editor_state.current_layer:
            print(f"Layer name: {self.editor_state.current_layer.name}")
            print(f"Layer locked: {self.editor_state.current_layer.locked}")
            print(f"Layer size: {self.editor_state.current_layer.width}x{self.editor_state.current_layer.height}")
        
        print(f"Tileset exists: {self.project.tileset is not None}")
        
        print("=========================\n")        
        self.statusbar.showMessage(f"Selected tile: {tile_id}")
    
    def _on_layer_selected(self, layer):
        """Handle layer selection"""
        self.editor_state.set_active_layer(layer)
        self.statusbar.showMessage(f"Active layer: {layer.name} [{layer.layer_type.value}]")

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
            QMessageBox.critical(self, "Error", f"Failed to open project:\n{str(e)}")
    
    def _save_project(self):
        """Save current project"""
        if self.project.project_path:
            try:
                ProjectIO.save_project(self.project, self.project.project_path)
                self.statusbar.showMessage(f"Saved: {self.project.project_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{str(e)}")
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
            QMessageBox.critical(self, "Error", f"Failed to save:\n{str(e)}")
    
    def _import_tileset(self):
        """Import tileset image"""
                # Force paint a visible tile
        self.project.layers[1].set_tile(0, 0, 1)

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
            QMessageBox.critical(self, "Error", f"Failed to import tileset:\n{str(e)}")
    
    def _subdivide_tiles(self):
        """Manually subdivide tiles"""
        if not self.project.tileset:
            QMessageBox.warning(self, "Warning", "No tileset loaded. Import a tileset first.")
            return
        
        current_size = self.project.tileset.tile_width
        
        dialog = TileSubdivisionDialog(current_size, self)
        if dialog.exec() == QDialog.Accepted:
            new_size = dialog.get_tile_size()
            
            if new_size == current_size:
                return
            
            try:
                # Re-slice with new tile size
                self.project.tileset.tile_width = new_size
                self.project.tileset.tile_height = new_size
                self.project.tileset.tiles.clear()
                self.project.tileset.slice_from_image()
                
                # Update project
                self.project.tile_width = new_size
                self.project.tile_height = new_size
                
                # Refresh palette
                self.tile_palette.set_tileset(self.project.tileset)
                
                self.statusbar.showMessage(
                    f"Tiles subdivided to {new_size}x{new_size} ({len(self.project.tileset.tiles)} tiles)"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to subdivide tiles:\n{str(e)}")
    
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
            QMessageBox.information(self, "Success", f"Exported to:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export:\n{str(e)}")
    
    def _export_png(self):
        """Export current view to PNG"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to PNG",
            f"{self.project.name}_render.png",
            "PNG Images (*.png)"
        )
        
        if not filename:
            return
        
        try:
            # Save pygame surface as PNG
            pygame.image.save(self.canvas.pygame_surface, filename)
            QMessageBox.information(self, "Success", f"Exported current view to:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PNG:\n{str(e)}")
    
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
            <li>Multi-layer tile editing (8 layer types)</li>
            <li>Auto-detect tile sizes (8x8, 16x16, 32x32, etc.)</li>
            <li>Manual tile subdivision</li>
            <li>Binary layer format with HDF5 export</li>
            <li>Paint, erase, fill, and picker tools</li>
            <li>PNG export for rendered views</li>
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
