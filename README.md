# MapleLegends ShopHelper

![MapleLegends ShopHelper](app_icon.png)

A specialized tool for MapleLegends players to manage their shop inventory, track item prices, and quickly identify items using OCR (Optical Character Recognition).

## Demo

https://github.com/tehboatler/ShopHelperv4/raw/main/demo_video/ShopHelperv4Demo.mp4

*Click the link above to download and watch a demonstration of ShopHelperv4 in action*

You can also view the demo video directly in the repository under the [demo_video](demo_video/) folder.

## Features

- **OCR Item Recognition**: Press F7 while hovering over item text in-game to capture and identify items
- **Inventory Management**: Track your shop inventory, including stock levels and pricing
- **Sales Ledger**: Record sales and track your shop's performance over time
- **Matched Item Display**: See instantly identified items in a fixed display area
- **Dark Mode Interface**: Easy on the eyes during long gaming sessions

## Installation Guide

### Running from Source (Recommended)

1. **Clone the Repository**:
   ```
   git clone https://github.com/tehboatler/ShopHelperv4.git
   cd ShopHelperv4
   ```

2. **Set Up Python Environment**:
   - Python 3.12.0 is required (the application has been tested with this version)
   - There are several ways to manage your Python environment:

     **Option A: Using pyenv (Recommended for managing multiple Python versions)**
     ```
     # Install Python 3.12.0 using pyenv
     pyenv install 3.12.0
     
     # Set local version for this project
     pyenv local 3.12.0
     ```

     **Option B: Using venv (Built into Python)**
     ```
     # Create a virtual environment in the project folder
     python -m venv venv
     
     # Activate the virtual environment:
     # On Windows:
     venv\Scripts\activate
     
     # On macOS/Linux:
     # source venv/bin/activate
     ```

3. **Install Dependencies**:
   ```
   # Make sure you're using Python 3.12.0 (check with python --version)
   pip install -r requirements.txt
   ```

4. **Run the Application**:
   ```
   python app.py
   ```

## Usage Guide

### First-Time Setup

1. **OCR Model Download**:
   - On first launch, the application will prompt you to download OCR models
   - Click "Download Models" and wait for the process to complete
   - This is a one-time download of approximately 20MB

2. **Configure Settings**:
   - Go to File → Settings to configure application preferences
   - Adjust match threshold, tooltip settings, and other options as needed

### Basic Usage

1. **Capturing Items**:
   - In-game, hover your cursor over item text
   - Press F7 to capture the text
   - The application will process the image, extract text, and attempt to match it to items in the database

2. **Managing Inventory**:
   - Use the Inventory tab to view and manage your shop items
   - Add new items, update stock levels, and adjust prices
   - Items that have never been sold will be highlighted in yellow

3. **Tracking Sales**:
   - When you sell an item, mark it as sold in the Inventory tab
   - The sale will be recorded in the ledger with timestamp and price information
   - View sales history in the Ledger tab

4. **Exporting Data**:
   - Go to File → Export Database to save your item database
   - This creates a backup that can be imported later if needed

## Troubleshooting

### Common Issues

1. **OCR Not Working**:
   - Ensure the OCR models were downloaded successfully
   - Try adjusting the preprocessing option in the settings
   - Make sure the text is clear and visible when capturing

2. **Application Crashes on Startup**:
   - Check if antivirus software is blocking the application
   - Try running as administrator
   - Verify that all dependencies are installed correctly

3. **Missing MKL Libraries**:
   - If you see errors about missing MKL libraries, they will be downloaded automatically on first run
   - If automatic download fails, you can download them manually from:
     https://github.com/intel/mkl-dnn/releases/download/v0.21/mklml_win_2019.0.5.20190502.zip
   - Extract the DLL files to the `libs` folder in the application directory

4. **Performance Issues**:
   - The application uses CPU-only mode for OCR by default
   - Close other resource-intensive applications for better performance
   - Ensure your system meets the minimum requirements (4GB RAM, Windows 10 or later)

### Getting Help

If you encounter issues not covered in this guide, please:
1. Check the known issues section in the repository
2. Submit a detailed bug report including:
   - Steps to reproduce the issue
   - Error messages (if any)
   - System specifications
   - Screenshots if applicable

## Development Information

### Project Structure

- `app.py` - Main application entry point
- `ocr_utils.py` - OCR processing utilities
- `item_database.py` - Item database management
- `inventory_ui.py` - Inventory UI components
- `ledger_ui.py` - Ledger UI components
- `tooltip_overlay.py` - Tooltip overlay functionality

### Dependencies

The application relies on several key libraries:
- PyQt6 for the GUI
- PaddleOCR for text recognition
- OpenCV and PIL for image processing
- Keyboard and MSS for screen capture
- FuzzyWuzzy for text matching
- Matplotlib for charts and visualizations

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PaddleOCR for the OCR engine
- PyQt6 for the GUI framework
- All contributors and testers who have helped improve this application
