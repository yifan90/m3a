import sys
import os

print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
# print(f"sys.path: {sys.path}")

try:
    import torch
    print(f"Torch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        try:
            print(f"CUDNN version: {torch.backends.cudnn.version()}")
        except Exception as e:
            print(f"Error checking CUDNN version: {e}")
except ImportError as e:
    print(f"Error importing torch: {e}")

try:
    from util import utils
    print("Successfully imported util.utils")
except ImportError as e:
    print(f"Error importing util.utils: {e}")
except Exception as e:
    print(f"Unexpected error importing util.utils: {e}")

try:
    from ultralytics import YOLO
    print("Successfully imported ultralytics")
except ImportError as e:
    print(f"Error importing ultralytics: {e}")
