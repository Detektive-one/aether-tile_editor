import os
from pathlib import Path
from .binary import BinaryLayerIO
from .metadata import MetadataIO
from .hdf5_exporter import HDF5Exporter

class ProjectIO:
    # \"\"\"Manage complete project save/load\"\"\"
    
    @staticmethod
    def save_project(project, directory: str):
        # \"\"\"Save project to directory (binary layers + JSON metadata)\"\"\"
        project_dir = Path(directory)
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create layers subdirectory
        layers_dir = project_dir / "layers"
        layers_dir.mkdir(exist_ok=True)
        
        # Save each layer as binary file
        for layer in project.layers:
            layer_path = layers_dir / f"{layer.name}.layer"
            BinaryLayerIO.save_layer(layer, str(layer_path))
        
        # Save metadata
        metadata_path = project_dir / "metadata.json"
        MetadataIO.save_metadata(project, str(metadata_path))
        
        # Store project path
        project.project_path = str(project_dir)
        
        return str(project_dir)
    
    @staticmethod
    def load_project(directory: str):
        # \"\"\"Load project from directory\"\"\"
        from core.models import MapProject, TileSet, LayerType
        import pygame
        
        project_dir = Path(directory)
        metadata_path = project_dir / "metadata.json"
        
        if not metadata_path.exists():
            raise FileNotFoundError(f"No metadata.json found in {directory}")
        
        # Load metadata
        metadata = MetadataIO.load_metadata(str(metadata_path))
        
        # Create project
        dims = metadata['dimensions']
        project = MapProject(
            name=metadata['project']['name'],
            grid_width=dims['grid_width'],
            grid_height=dims['grid_height'],
            tile_width=dims['tile_width'],
            tile_height=dims['tile_height']
        )
        project.project_path = str(project_dir)
        
        # Load tileset
        if metadata.get('tileset'):
            ts_meta = metadata['tileset']
            tileset_path = ts_meta['path']
            
            # Try relative path first
            if not Path(tileset_path).exists():
                tileset_path = project_dir / Path(tileset_path).name
            
            if Path(tileset_path).exists():
                tileset = TileSet(
                    name=ts_meta['name'],
                    image_path=str(tileset_path),
                    tile_width=ts_meta['tile_width'],
                    tile_height=ts_meta['tile_height']
                )
                tileset.slice_from_image()
                project.tileset = tileset
        
        # Load layers
        layers_dir = project_dir / "layers"
        for layer_meta in metadata.get('layers', []):
            layer_file = layers_dir / layer_meta['file']
            
            if layer_file.exists():
                layer = BinaryLayerIO.load_layer(str(layer_file))
                layer.name = layer_meta['name']
                layer.layer_type = LayerType(layer_meta['type'])
                layer.visible = layer_meta.get('visible', True)
                layer.locked = layer_meta.get('locked', False)
                layer.opacity = layer_meta.get('opacity', 1.0)
                layer.z_index = layer_meta.get('z_index', 0)
                layer.interacts_with_layers = layer_meta.get('interacts_with_layers', True)
                
                project.layers.append(layer)
        
        # Sort by z_index
        project.layers.sort(key=lambda l: l.z_index)
        
        return project
    
    @staticmethod
    def export_to_hdf5(project, filepath: str):
        # \"\"\"Export project to HDF5 file\"\"\"
        HDF5Exporter.export_project(project, filepath)
    
    @staticmethod
    def import_from_hdf5(filepath: str):
        # \"\"\"Import project from HDF5 file\"\"\"
        return HDF5Exporter.import_project(filepath)
