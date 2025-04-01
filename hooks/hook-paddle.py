
import os
import sys

# Add the executable directory to PATH to find MKL libraries
if hasattr(sys, '_MEIPASS'):
    os.environ['PATH'] = sys._MEIPASS + os.pathsep + os.environ.get('PATH', '')
