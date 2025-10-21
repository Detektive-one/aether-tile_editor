from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QListWidget, QListWidgetItem, QPushButton,
                               QLabel, QCheckBox, QSlider, QComboBox,
                               QInputDialog, QMessageBox)
from PySide6.QtCore import Signal, Qt
from core.models import LayerType

class LayerPanelWidget(QWidget):
    # """Panel for managing layers"""
    
    layer_selected = Signal(object)  # layer
    layer_visibility_changed = Signal(object, bool)  # layer, visible
    layers_changed = Signal()  # Layers modified
    
    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.current_layer = None
        
        self._setup_ui()
        self._populate_layers()
    
    def _setup_ui(self):
        # """Setup UI"""
        layout = QVBoxLayout(self)
        
        # Layer list
        self.layer_list = QListWidget()
        self.layer_list.setSelectionMode(QListWidget.SingleSelection)
        self.layer_list.itemClicked.connect(self._on_layer_clicked)
        layout.addWidget(QLabel("Layers:"))
        layout.addWidget(self.layer_list)
        
        # Layer controls
        controls_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("+ Add")
        self.btn_add.clicked.connect(self._on_add_layer)
        controls_layout.addWidget(self.btn_add)
        
        self.btn_delete = QPushButton("- Delete")
        self.btn_delete.clicked.connect(self._on_delete_layer)
        controls_layout.addWidget(self.btn_delete)
        
        layout.addLayout(controls_layout)
        
        # Layer properties
        props_layout = QVBoxLayout()
        
        # Visibility checkbox
        self.chk_visible = QCheckBox("Visible")
        self.chk_visible.setChecked(True)
        self.chk_visible.stateChanged.connect(self._on_visibility_changed)
        props_layout.addWidget(self.chk_visible)
        
        # Locked checkbox
        self.chk_locked = QCheckBox("Locked")
        self.chk_locked.stateChanged.connect(self._on_locked_changed)
        props_layout.addWidget(self.chk_locked)
        
        # Interacts checkbox
        self.chk_interacts = QCheckBox("Interacts with other layers")
        self.chk_interacts.setChecked(True)
        self.chk_interacts.stateChanged.connect(self._on_interacts_changed)
        props_layout.addWidget(self.chk_interacts)
        
        # Opacity slider
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity:"))
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setMinimum(0)
        self.slider_opacity.setMaximum(100)
        self.slider_opacity.setValue(100)
        self.slider_opacity.valueChanged.connect(self._on_opacity_changed)
        opacity_layout.addWidget(self.slider_opacity)
        props_layout.addLayout(opacity_layout)
        
        layout.addLayout(props_layout)
    
    def _populate_layers(self):
        # """Populate layer list"""
        self.layer_list.clear()
        
        # Sort by z_index (highest first for visual order)
        sorted_layers = sorted(self.project.layers, key=lambda l: -l.z_index)
        
        for layer in sorted_layers:
            icon = "👁" if layer.visible else "  "
            lock_icon = "🔒" if layer.locked else ""
            item_text = f"{icon} {lock_icon} {layer.name} [{layer.layer_type.value}]"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, layer)
            self.layer_list.addItem(item)
    
    def _on_layer_clicked(self, item):
        # """Handle layer selection"""
        layer = item.data(Qt.UserRole)
        self.current_layer = layer
        
        # Update properties UI
        self.chk_visible.setChecked(layer.visible)
        self.chk_locked.setChecked(layer.locked)
        self.chk_interacts.setChecked(layer.interacts_with_layers)
        self.slider_opacity.setValue(int(layer.opacity * 100))
        
        # Emit signal
        self.layer_selected.emit(layer)
    
    def _on_add_layer(self):
        # """Add new layer"""
        # Show dialog for layer name and type
        name, ok = QInputDialog.getText(self, "Add Layer", "Layer name:")
        if not ok or not name:
            return
        
        # Create layer
        layer = self.project.add_layer(name, LayerType.ACTUAL)
        
        # Refresh list
        self._populate_layers()
        self.layers_changed.emit()
    
    def _on_delete_layer(self):
        # """Delete selected layer"""
        if not self.current_layer:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            'Delete Layer',
            f'Delete layer "{self.current_layer.name}"?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.project.remove_layer(self.current_layer)
            self.current_layer = None
            self._populate_layers()
            self.layers_changed.emit()
    
    def _on_visibility_changed(self, state):
        # """Handle visibility change"""
        if self.current_layer:
            self.current_layer.visible = (state == Qt.Checked)
            self._populate_layers()
            self.layer_visibility_changed.emit(self.current_layer, self.current_layer.visible)
    
    def _on_locked_changed(self, state):
        # """Handle locked change"""
        if self.current_layer:
            self.current_layer.locked = (state == Qt.Checked)
            self._populate_layers()
    
    def _on_interacts_changed(self, state):
        # """Handle interacts change"""
        if self.current_layer:
            self.current_layer.interacts_with_layers = (state == Qt.Checked)
    
    def _on_opacity_changed(self, value):
        # """Handle opacity change"""
        if self.current_layer:
            self.current_layer.opacity = value / 100.0
    
    def refresh(self):
        # """Refresh layer list"""
        self._populate_layers()
