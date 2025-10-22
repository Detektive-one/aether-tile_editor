import struct
import numpy as np
from pathlib import Path
from typing import Optional
import zlib

class BinaryLayerIO:
    # \"\"\"Save/load layer data in binary format\"\"\"
    
    MAGIC = b'AELR'
    VERSION = 1
    HEADER_SIZE = 32
    
    @staticmethod
    def save_layer(layer, filepath: str, compress: bool = True):
        # \"\"\"Save layer to binary file\"\"\"
        with open(filepath, 'wb') as f:
            # Write header
            compression_flag = 1 if compress else 0
            header = struct.pack(
                '<4sIIIB15x',  # < = little-endian, x = padding
                BinaryLayerIO.MAGIC,
                BinaryLayerIO.VERSION,
                layer.width,
                layer.height,
                compression_flag
            )
            f.write(header)
            
            # Write tile grid data
            grid_bytes = layer.tile_grid.tobytes()
            
            if compress:
                grid_bytes = zlib.compress(grid_bytes, level=6)
            
            f.write(grid_bytes)
    
    @staticmethod
    def load_layer(filepath: str):
        # \"\"\"Load layer from binary file\"\"\"
        from core.models import Layer, LayerType
        
        with open(filepath, 'rb') as f:
            # Read header
            header_data = f.read(BinaryLayerIO.HEADER_SIZE)
            magic, version, width, height, compression = struct.unpack(
                '<4sIIIB15x',
                header_data
            )
            
            # Validate
            if magic != BinaryLayerIO.MAGIC:
                raise ValueError(f"Invalid file format: {magic}")
            
            if version != BinaryLayerIO.VERSION:
                raise ValueError(f"Unsupported version: {version}")
            
            # Read tile grid
            grid_bytes = f.read()
            
            # Decompress if needed
            if compression == 1:
                grid_bytes = zlib.decompress(grid_bytes)
            
            # Convert to numpy array
            tile_grid = np.frombuffer(grid_bytes, dtype=np.int32)
            tile_grid = tile_grid.reshape((height, width))
            
            # Create layer object
            layer_name = Path(filepath).stem
            layer = Layer(layer_name, width, height)
            layer.tile_grid = tile_grid
            
            return layer


