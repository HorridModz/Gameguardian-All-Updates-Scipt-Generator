import sys
import os
sys.path.append((os.path.dirname(__file__)))

from build_android import build


if __name__ == "__main__":
    build(debug=True)
