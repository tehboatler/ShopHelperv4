"""
PyInstaller hook for PaddleOCR
This hook helps PyInstaller find all the necessary files for PaddleOCR
"""

import os
import sys
import glob
import paddle
import paddleocr
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the Paddle installation directory
paddle_dir = os.path.dirname(paddle.__file__)

# Get the PaddleOCR installation directory
paddleocr_dir = os.path.dirname(paddleocr.__file__)

# Collect all PaddleOCR submodules
hiddenimports = collect_submodules('paddleocr')
hiddenimports.extend(collect_submodules('paddle'))
hiddenimports.extend([
    'paddle.fluid.core',
    'paddle.fluid.framework',
    'paddle.inference',
    'paddleocr.tools.infer.predict_system',
    'paddleocr.tools.infer.predict_det',
    'paddleocr.tools.infer.predict_rec',
    'paddleocr.tools.infer.utility',
])

# Collect all DLL files from paddle directory
paddle_dlls = []
for root, dirs, files in os.walk(paddle_dir):
    for file in files:
        if file.endswith('.dll') or file.endswith('.so'):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, os.path.dirname(paddle_dir))
            paddle_dlls.append((full_path, os.path.dirname(rel_path)))

# Collect all data files
datas = collect_data_files('paddleocr')

# Add MKL DLLs explicitly
mkl_dlls = []
for pattern in ['*mkl*.dll', '*mklml*.dll', 'libiomp*.dll', 'iomp*.dll']:
    for dll in glob.glob(os.path.join(paddle_dir, pattern)):
        if os.path.isfile(dll):
            mkl_dlls.append((dll, '.'))
    # Also look in paddle/libs directory
    for dll in glob.glob(os.path.join(paddle_dir, 'libs', pattern)):
        if os.path.isfile(dll):
            mkl_dlls.append((dll, '.'))

# Combine all data files
datas.extend(paddle_dlls)
datas.extend(mkl_dlls)

# Print summary for debugging
print(f"PaddleOCR hook: Found {len(hiddenimports)} modules to import")
print(f"PaddleOCR hook: Found {len(datas)} data files to include")
