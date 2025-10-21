import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

class MetadataIO:
    # \"\"\"Save/load project metadata as JSON\"\"\"
    
    @staticmethod
    def save_metadata(project, filepath: str):
        # \"\"\"Save project metadata to JSON\"\"\"
        from core.models import LayerType
        
        metadata = {
            'project': {
                'name': project.name,
                'version': '1.0',
                'created': datetime.now().isoformat(),
                'editor_version': '1.0.0'
            },
            'dimensions': {
                'grid_width': project.grid_width,
                'grid_height': project.grid_height,
                'tile_width': project.tile_width,
                'tile_height': project.tile_height
            },
            'tileset': None,
            'layers': []
        }
        
        # Add tileset info
        if project.tileset:
            metadata['tileset'] = {
                'name': project.tileset.name,
                'path': project.tileset.image_path,
                'tile_width': project.tileset.tile_width,
                'tile_height': project.tileset.tile_height,
                'tile_count': len(project.tileset.tiles)
            }
        
        # Add layer info
        for layer in project.layers:
            layer_data = {
                'name': layer.name,
                'type': layer.layer_type.value,
                'file': f"{layer.name}.layer",
                'visible': layer.visible,
                'locked': layer.locked,
                'opacity': layer.opacity,
                'z_index': layer.z_index,
                'interacts_with_layers': layer.interacts_with_layers
            }
            metadata['layers'].append(layer_data)
        
        # Write JSON
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    @staticmethod
    def load_metadata(filepath: str) -> Dict[str, Any]:
        # \"\"\"Load metadata from JSON file\"\"\"
        with open(filepath, 'r') as f:
            return json.load(f)


