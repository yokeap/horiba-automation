# Horiba Automation System - Installation Guide

## Prerequisites

- Python 3.8 or higher
- Windows OS (for AutoIt support)
- Administrator privileges (for some automation features)

## Installation Steps

### 1. Install Python Dependencies

Open Command Prompt or PowerShell as Administrator and run:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
# Core GUI
pip install PyQt6

# Image Recognition (CRITICAL - Required for reliable image detection)
pip install opencv-python pillow

# Automation
pip install pyautogui PyAutoIt

# Serial Communication
pip install pyserial
```

### 2. Verify OpenCV Installation

Run this test to verify OpenCV is installed correctly:

```python
import cv2
print(f"OpenCV version: {cv2.__version__}")
print("OpenCV installed successfully!")
```

If you see version number, you're good to go!

### 3. Install AutoIt (if not already installed)

PyAutoIt requires AutoIt to be installed on your system:

1. Download from: https://www.autoitscript.com/site/autoit/downloads/
2. Install AutoIt3
3. Restart your computer

## Common Installation Issues

### Issue 1: "No module named 'cv2'"

**Solution:**
```bash
pip uninstall opencv-python
pip install opencv-python
```

Or try the headless version:
```bash
pip install opencv-python-headless
```

### Issue 2: PyAutoIt not working

**Solution:**
1. Ensure AutoIt is installed on your system
2. Reinstall PyAutoIt:
```bash
pip uninstall PyAutoIt
pip install PyAutoIt
```

### Issue 3: PyQt6 import errors

**Solution:**
```bash
pip uninstall PyQt6 PyQt6-Qt6
pip install PyQt6
```

### Issue 4: Permission errors during installation

**Solution:**
Run Command Prompt as Administrator, or use:
```bash
pip install --user -r requirements.txt
```

## Testing Your Installation

### Quick Test Script

Create a file `test_installation.py`:

```python
import sys

def test_imports():
    """Test all required imports"""
    errors = []
    
    # Test PyQt6
    try:
        from PyQt6.QtWidgets import QApplication
        print("✓ PyQt6 installed")
    except ImportError as e:
        errors.append(f"✗ PyQt6 missing: {e}")
    
    # Test OpenCV (CRITICAL)
    try:
        import cv2
        print(f"✓ OpenCV installed (version {cv2.__version__})")
    except ImportError as e:
        errors.append(f"✗ OpenCV missing (CRITICAL): {e}")
    
    # Test PIL/Pillow
    try:
        from PIL import Image
        print("✓ Pillow installed")
    except ImportError as e:
        errors.append(f"✗ Pillow missing: {e}")
    
    # Test PyAutoGUI
    try:
        import pyautogui
        print("✓ PyAutoGUI installed")
    except ImportError as e:
        errors.append(f"✗ PyAutoGUI missing: {e}")
    
    # Test PyAutoIt
    try:
        import autoit
        print("✓ PyAutoIt installed")
    except ImportError as e:
        errors.append(f"✗ PyAutoIt missing: {e}")
    
    # Test PySerial
    try:
        import serial
        print("✓ PySerial installed")
    except ImportError as e:
        errors.append(f"✗ PySerial missing: {e}")
    
    if errors:
        print("\n" + "="*50)
        print("ERRORS FOUND:")
        for error in errors:
            print(error)
        print("="*50)
        return False
    else:
        print("\n" + "="*50)
        print("✓ All dependencies installed successfully!")
        print("="*50)
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
```

Run it:
```bash
python test_installation.py
```

## Project Structure

```
horiba-automation/
├── main.py                 # Main GUI application
├── mesa.py                 # Mesa automation logic
├── requirements.txt        # Python dependencies
├── image_utility.py        # Image capture utility
├── test_installation.py    # Installation test script
└── imgdata/               # Image files for automation
    ├── bt_cal_energy_copy.png
    ├── _0_btCancel.png
    ├── _1_ltProjectOpen.png
    ├── _2_btEGATCal.png
    ├── _2_1_ready.png
    ├── _3_btReport.png
    ├── _4_btExport.png
    ├── _5_ddExcel.png
    ├── _6_btClose.png
    ├── bt_warmup.png
    ├── bt_egat_15kv.png
    └── bt_egat_50kv.png
```

## Running the Application

### First Time Setup

1. Capture UI images:
```bash
python image_utility.py
```
- Select option 2 for batch capture
- Follow prompts to capture all UI elements

2. Test image detection:
```bash
python image_utility.py
```
- Select option 3 to test each image
- Verify detection works at confidence 0.7-0.8

### Running the Main Application

```bash
python main.py
```

## Troubleshooting

### Application won't start

1. Check Python version:
```bash
python --version
```
Should be 3.8 or higher

2. Verify all imports work:
```bash
python test_installation.py
```

3. Check for error messages in console

### Image detection not working

1. **CRITICAL**: Ensure OpenCV is installed:
```bash
python -c "import cv2; print(cv2.__version__)"
```

2. Recapture images using `image_utility.py`

3. Lower confidence levels in code (0.6-0.7)

4. Check IMAGE_DETECTION_GUIDE.md for more tips

### Serial port not connecting

1. Check COM port in Device Manager
2. Update COM port in main.py:
```python
self.mesaApp = mesa.mesa("COM4")  # Change COM4 to your port
```
3. Verify port isn't in use by another application

## System Requirements

### Minimum:
- Windows 10
- Python 3.8
- 4GB RAM
- 100MB free disk space

### Recommended:
- Windows 10/11
- Python 3.10+
- 8GB RAM
- SSD for faster image processing

## Getting Help

If you encounter issues:

1. Check console output for error messages
2. Review IMAGE_DETECTION_GUIDE.md
3. Run test_installation.py to verify setup
4. Check that all image files exist in imgdata/

## Important Notes

### OpenCV is CRITICAL

Without OpenCV (`opencv-python`), the application will work but with limitations:
- ✗ No confidence-based matching
- ✗ Lower detection reliability
- ✗ Slower image matching
- ✓ Basic exact matching still works

**Always install OpenCV for production use!**

### Image Files

All image files in `imgdata/` must be:
- PNG format
- Captured from the same system/resolution
- Captured at 100% window zoom
- High quality (not blurry)

### COM Port

Update the COM port in `main.py` to match your system:
```python
self.mesaApp = mesa.mesa("COM4")  # Your actual COM port
```

Check Device Manager → Ports (COM & LPT) to find your port number.

## Update Instructions

To update the application:

1. Backup your `imgdata/` folder
2. Replace main.py and mesa.py with new versions
3. Run `pip install -r requirements.txt --upgrade`
4. Test with `python test_installation.py`

## License & Support

For technical support, refer to the documentation or contact your system administrator.
