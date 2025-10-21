import h5py
import json
import numpy as np
from pathlib import Path
import io

class HDF5Exporter:
    # \"\"\"Export/import entire project to/from HDF5 container\"\"\"
    
    @staticmethod
    def export_project(project, filepath: str):
        # \"\"\"Export MapProject to HDF5 file\"\"\"
        from core.models import LayerType
        
        with h5py.File(filepath, 'w') as f:
            # Create groups
            tileset_group = f.create_group('tileset')
            layers_group = f.create_group('layers')
            
            # Save project metadata
            metadata = {
                'project': {
                    'name': project.name,
                    'version': '1.0'
                },
                'dimensions': {
                    'grid_width': project.grid_width,
                    'grid_height': project.grid_height,
                    'tile_width': project.tile_width,
                    'tile_height': project.tile_height
                }
            }
            
            f.create_dataset(
                'project_metadata',
                data=json.dumps(metadata, indent=2),
                dtype=h5py.string_dtype()
            )
            
            # Save tileset
            if project.tileset and project.tileset.image:
                # Save image as bytes
                if Path(project.tileset.image_path).exists():
                    with open(project.tileset.image_path, 'rb') as img_file:
                        image_bytes = img_file.read()
                        tileset_group.create_dataset(
                            'image',
                            data=np.frombuffer(image_bytes, dtype=np.uint8)
                        )
                
                # Save tileset metadata
                tileset_meta = {
                    'name': project.tileset.name,
                    'path': project.tileset.image_path,
                    'tile_width': project.tileset.tile_width,
                    'tile_height': project.tileset.tile_height
                }
                
                tileset_group.create_dataset(
                    'metadata',
                    data=json.dumps(tileset_meta),
                    dtype=h5py.string_dtype()
                )
                
                # Save tile definitions
                tile_defs = {
                    str(tid): tile.to_dict()
                    for tid, tile in project.tileset.tiles.items()
                }
                
                tileset_group.create_dataset(
                    'tile_definitions',
                    data=json.dumps(tile_defs),
                    dtype=h5py.string_dtype()
                )
            
            # Save each layer
            for layer in project.layers:
                layer_group = layers_group.create_group(layer.name)
                
                # Save tile grid
                layer_group.create_dataset(
                    'tile_grid',
                    data=layer.tile_grid,
                    compression='gzip',
                    compression_opts=6
                )
                
                # Save layer properties
                properties = {
                    'name': layer.name,
                    'type': layer.layer_type.value,
                    'visible': layer.visible,
                    'locked': layer.locked,
                    'opacity': layer.opacity,
                    'z_index': layer.z_index,
                    'interacts_with_layers': layer.interacts_with_layers
                }
                
                layer_group.create_dataset(
                    'properties',
                    data=json.dumps(properties),
                    dtype=h5py.string_dtype()
                )
    
    @staticmethod
    def import_project(filepath: str):
        # \"\"\"Load MapProject from HDF5 file\"\"\"
        from core.models import MapProject, Layer, TileSet, TileData, LayerType
        import pygame
        
        with h5py.File(filepath, 'r') as f:
            # Load project metadata
            metadata = json.loads(f['project_metadata'][()])
            
            # Create project
            project = MapProject(
                name=metadata['project']['name'],
                grid_width=metadata['dimensions']['grid_width'],
                grid_height=metadata['dimensions']['grid_height'],
                tile_width=metadata['dimensions']['tile_width'],
                tile_height=metadata['dimensions']['tile_height']
            )
            
            # Load tileset
            if 'tileset' in f:
                tileset_meta = json.loads(f['tileset/metadata'][()])
                
                # Load image from bytes
                if 'image' in f['tileset']:
                    image_bytes = bytes(f['tileset/image'][:])
                    image_surface = pygame.image.load(io.BytesIO(image_bytes))
                    
                    tileset = TileSet(
                        name=tileset_meta['name'],
                        image_path=tileset_meta['path'],
                        tile_width=tileset_meta['tile_width'],
                        tile_height=tileset_meta['tile_height']
                    )
                    tileset.image = image_surface
                    
                    # Load tile definitions
                    if 'tile_definitions' in f['tileset']:
                        tile_defs = json.loads(f['tileset/tile_definitions'][()])
                        for tid_str, tdef in tile_defs.items():
                            tid = int(tid_str)
                            tileset.tiles[tid] = TileData.from_dict(tdef)
                    
                    project.tileset = tileset
            
            # Load layers
            if 'layers' in f:
                for layer_name in f['layers'].keys():
                    layer_group = f['layers'][layer_name]
                    
                    # Load properties
                    props = json.loads(layer_group['properties'][()])
                    
                    # Create layer
                    layer_type = LayerType(props['type'])
                    layer = Layer(
                        props['name'],
                        project.grid_width,
                        project.grid_height,
                        layer_type
                    )
                    layer.visible = props['visible']
                    layer.locked = props.get('locked', False)
                    layer.opacity = props.get('opacity', 1.0)
                    layer.z_index = props['z_index']
                    layer.interacts_with_layers = props.get('interacts_with_layers', True)
                    
                    # Load tile grid
                    layer.tile_grid = layer_group['tile_grid'][:]
                    
                    project.layers.append(layer)
            
            # Sort layers by z_index
            project.layers.sort(key=lambda l: l.z_index)
            
            return project


