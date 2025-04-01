# MapleLegends ShopHelper

![MapleLegends ShopHelper](app_icon.png)

A specialized tool for MapleLegends players to manage their shop inventory, track item prices, and quickly identify items using OCR (Optical Character Recognition).

## Demo

![Demo Video](demo_video/Shophelperv4demo.webm)

## Features

- **OCR Item Recognition**: Press F7 while hovering over item text in-game to capture and identify items
- **Inventory Management**: Track your shop inventory, including stock levels and pricing
- **Sales Ledger**: Record sales and track your shop's performance over time
- **Matched Item Display**: See instantly identified items in a fixed display area
- **Dark Mode Interface**: Easy on the eyes during long gaming sessions

## Usage Guide

### Adding New Items To Your Database

#### 1. Set Match Confidence Threshold to 0%
![Set Match Confidence](demo_video/Pasted%20image%2020250401144651.png)

This is to ensure the OCR doesn't exclude new unrecognized strings of text.
*(note: when not adding new items to the database, its better quality of life to have the setting sit on 90%, so remember to switch it back!)*

#### 2. Hover over the scroll/item you want to match and press F7
![Hover and Press F7](demo_video/Pasted%20image%2020250401145013.png)

This will generate a new log in your Recently Logged Items tab
![New Log](demo_video/Pasted%20image%2020250401145046.png)

#### 3. Double-click the Matched Item cell and a dialogue will appear:
![Item Dialog](demo_video/Pasted%20image%2020250401145313.png)

Ensure the Item string is correct and enter a price for the item

### Adjusting the stock of items

Right clicking the row of the item, or double-clicking the stock cell of an item will bring up a Stock Adjustment dialogue:

![Stock Adjustment 1](demo_video/Pasted%20image%2020250401145742.png)
![Stock Adjustment 2](demo_video/Pasted%20image%2020250401145753.png)

Adjust stock as you see fit and it'll be reflected in your Inventory tab:
![Inventory Tab](demo_video/Pasted%20image%2020250401145832.png)

### Use Cases

#### Quick Shop Restocking
The prices you set can be set to be copied to clipboard after matching items. This makes it super easy to put stock up in your shop with the prices you've set.

![Quick Restocking](demo_video/Pasted%20image%2020250401150007.png)

#### Tracking Last Sold Dates and Adjusting Prices for Sellability
Items that you've never logged as sold will appear in yellow text along with the price they last sold at. 
![Tracking Sales](demo_video/Pasted%20image%2020250401150155.png)

For convenience, you can decrement the price from a context menu by right clicking the item in the inventory tab:
![Price Adjustment 1](demo_video/Pasted%20image%2020250401150433.png)
![Price Adjustment 2](demo_video/Pasted%20image%2020250401150444.png)

### Sweaty Ledger Stuff
Explore this tab at your own leisure if you're sweaty enough:
![Ledger](demo_video/Pasted%20image%2020250401150617.png)

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
