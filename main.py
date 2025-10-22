 #!/usr/bin/env python3
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import TileEditorMainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Aether Tile Editor")
    app.setOrganizationName("Aether Framework")
    window = TileEditorMainWindow()
    window.show()
    sys.exit(app.exec())
if __name__ == "__main__":
    main()