"""
Build script for MapleLegends ShopHelper using the collect-all approach
This script creates a standalone executable using PyInstaller with collect-all flags
"""

import os
import sys
import shutil
import time
import glob
import PyInstaller.__main__
import site
from pathlib import Path
import requests
import io
import zipfile

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define the output directory
output_dir = os.path.join(current_dir, 'dist')
output_name = 'MapleLegends_ShopHelper'

# Try to clean up previous builds, but don't fail if we can't
try:
    if os.path.exists(output_dir):
        print("Attempting to clean up previous build...")
        shutil.rmtree(output_dir)
        print("Successfully cleaned up previous build.")
except PermissionError:
    print("Warning: Could not remove previous build directory. It may be in use.")
    print("Will attempt to build anyway with a different output name.")
    # Modify the output name to avoid conflicts
    output_name = f'MapleLegends_ShopHelper_{int(time.time())}'

# Create a libs directory for MKL libraries
libs_dir = os.path.join(current_dir, 'libs')
os.makedirs(libs_dir, exist_ok=True)

# Check if MKL libraries need to be downloaded
mkl_files = glob.glob(os.path.join(libs_dir, 'mklml*.dll'))
if not mkl_files:
    print("MKL libraries not found. Downloading them...")
    try:
        # URL for Intel MKL libraries (using a known source)
        mkl_url = "https://github.com/intel/mkl-dnn/releases/download/v0.21/mklml_win_2019.0.5.20190502.zip"
        
        # Download the MKL package
        print(f"Downloading MKL libraries from {mkl_url}")
        response = requests.get(mkl_url, stream=True)
        response.raise_for_status()
        
        # Extract the ZIP file
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            # Extract only the DLL files
            for file in zip_ref.namelist():
                if file.endswith('.dll'):
                    print(f"Extracting {file} to {libs_dir}")
                    zip_ref.extract(file, libs_dir)
        
        print("MKL libraries downloaded and extracted successfully.")
    except Exception as e:
        print(f"Error downloading MKL libraries: {str(e)}")
        print("Will continue build without MKL libraries. The application may not work correctly.")

# Find PaddleOCR model files
site_packages = site.getsitepackages()[0]
paddleocr_path = os.path.join(site_packages, 'paddleocr')
model_files = []

# Look for model files in the PaddleOCR directory
if os.path.exists(paddleocr_path):
    for root, dirs, files in os.walk(paddleocr_path):
        for file in files:
            if file.endswith('.pdmodel') or file.endswith('.pdiparams') or file.endswith('.pdiparams.info'):
                model_path = os.path.join(root, file)
                rel_path = os.path.relpath(os.path.dirname(model_path), site_packages)
                model_files.append((model_path, rel_path))
                print(f"Found model file: {model_path} -> {rel_path}")

# Look for model files in the local models directory
local_models_path = os.path.join(current_dir, 'models')
if os.path.exists(local_models_path):
    print(f"Checking local models directory: {local_models_path}")
    for root, dirs, files in os.walk(local_models_path):
        for file in files:
            if file.endswith('.pdmodel') or file.endswith('.pdiparams') or file.endswith('.pdiparams.info'):
                model_path = os.path.join(root, file)
                # For local models, we want to preserve the directory structure relative to the app
                rel_path = os.path.relpath(os.path.dirname(model_path), current_dir)
                model_files.append((model_path, rel_path))
                print(f"Found local model file: {model_path} -> {rel_path}")

# Find Paddle libraries in site-packages
paddle_libs = []
paddle_path = os.path.join(site_packages, 'paddle')
if os.path.exists(paddle_path):
    print(f"Checking Paddle libraries in {paddle_path}")
    for root, dirs, files in os.walk(paddle_path):
        for file in files:
            if file.endswith('.dll') or file.endswith('.so'):
                lib_path = os.path.join(root, file)
                rel_path = os.path.relpath(os.path.dirname(lib_path), site_packages)
                paddle_libs.append((lib_path, rel_path))
                print(f"Found Paddle library: {lib_path} -> {rel_path}")

# Create the data files argument
data_files = [
    '--add-data=*.json;.',                     # Include JSON files
    '--add-data=*.png;.',                      # Include PNG files
    '--add-data=*.ico;.',                      # Include ICO files
]

# Add model files to data_files
for model_path, rel_path in model_files:
    data_files.append(f'--add-data={model_path};{rel_path}')

# Add Paddle libraries to data_files
for lib_path, rel_path in paddle_libs:
    data_files.append(f'--add-data={lib_path};{rel_path}')

# Add MKL libraries from the libs directory
for file in glob.glob(os.path.join(libs_dir, '*.dll')):
    data_files.append(f'--add-data={file};.')
    print(f"Adding MKL library to package: {file}")

# Create the build command using collect-all flags as mentioned in issue #11342
build_args = [
    'app.py',                                  # Main script
    f'--name={output_name}',                   # Output name
    '--console',                              # No console window for release (change to --console for debugging)
    '--icon=app.ico',                          # Application icon
]

# Add data files
build_args.extend(data_files)

# Add collect-all arguments
collect_all_modules = [
    'paddleocr',
    'pyclipper',
    'fuzzywuzzy',
    'keyboard',
    'mss',
    'PIL',
    'pyautogui',
    'numpy',
    'cv2',
]

for module in collect_all_modules:
    build_args.append(f'--collect-all={module}')

# Add hidden imports
hidden_imports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'scipy.special',
    'scipy.special._ufuncs',
    'scipy.linalg.cython_blas',
    'scipy.linalg.cython_lapack',
    'scipy.sparse.csgraph._validation',
    'scipy._lib.messagestream',
    'pandas',
    'shapely',
    'paddle.fluid.core',
]

for imp in hidden_imports:
    build_args.append(f'--hidden-import={imp}')

# Add runtime hooks to set PATH for MKL libraries
runtime_hooks_dir = os.path.join(current_dir, 'hooks')
os.makedirs(runtime_hooks_dir, exist_ok=True)

# Create a runtime hook to set PATH
hook_path = os.path.join(runtime_hooks_dir, 'hook-paddle.py')
with open(hook_path, 'w') as f:
    f.write("""
import os
import sys

# Add the executable directory to PATH to find MKL libraries
if hasattr(sys, '_MEIPASS'):
    os.environ['PATH'] = sys._MEIPASS + os.pathsep + os.environ.get('PATH', '')
""")

build_args.append(f'--runtime-hook={hook_path}')

# Final arguments
build_args.extend([
    '--noconfirm',                             # Don't ask for confirmation
    '--clean',                                 # Clean PyInstaller cache
])

# Run PyInstaller
print("Building MapleLegends ShopHelper executable...")
print(f"Build command: pyinstaller {' '.join(build_args)}")
PyInstaller.__main__.run(build_args)

print(f"\nBuild complete! Executable is in the 'dist/{output_name}' folder.")
