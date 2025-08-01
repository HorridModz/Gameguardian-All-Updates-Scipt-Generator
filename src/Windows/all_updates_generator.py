# Add src to system path for relative imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from cli import main


if __name__ == "__main__":
    main()
