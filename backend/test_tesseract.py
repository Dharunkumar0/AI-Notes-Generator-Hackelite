import pytesseract
try:
    version = pytesseract.get_tesseract_version()
    print(f"Tesseract version: {version}")
    print("Tesseract OCR is properly installed!")
except Exception as e:
    print(f"Error: {str(e)}")
    print("\nPlease ensure Tesseract OCR is installed and the path is set correctly.")
    print("Download Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki")
