# Tesseract OCR Setup for Portal Results Parsing

The portal results parser uses Tesseract OCR to extract text from the daily BI email images.

## Windows Installation

1. **Download Tesseract installer:**
   - Visit: https://github.com/UB-Mannheim/tesseract/wiki
   - Download: `tesseract-ocr-w64-setup-5.3.x.exe` (latest version)

2. **Install Tesseract:**
   - Run the installer
   - **IMPORTANT:** During installation, note the install path (usually `C:\Program Files\Tesseract-OCR`)
   - Make sure to check "Add to PATH" during installation

3. **Verify Installation:**
   ```bash
   tesseract --version
   ```

4. **Configure Python to find Tesseract:**

   If Tesseract is not in PATH, add this to your environment or update the code:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

## Testing

Once installed, the portal parser will automatically:
1. Detect BI emails from `c00605mgr@chilis.com`
2. Extract image attachments
3. Run OCR to extract text
4. Parse metrics (Sales, Labor %, Guest Satisfaction, etc.)
5. Store in database
6. Include in daily digest

## Troubleshooting

- **"Tesseract not found" error:** Make sure Tesseract is installed and in PATH
- **OCR accuracy issues:** The parser expects specific keywords like "sales", "labor", "guest satisfaction"
- **No metrics found:** Check `portal_metrics` table - the raw OCR text is stored for debugging

## Manual Testing

To test with a specific BI email thread:
```bash
curl http://localhost:8002/api/parse-portal-email?thread_id=YOUR_THREAD_ID
```
