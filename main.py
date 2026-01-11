import sys
from PyQt5.QtWidgets import QApplication
from src.app import GifCompareApp


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = GifCompareApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
