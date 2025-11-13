# Portal Results Parser - Daily BI Email Integration

## Overview
Automatically parses your daily Business Intelligence email from `c00605mgr@chilis.com` containing portal results as an image. Uses OCR to extract metrics and includes them in your Daily Brief.

## What It Does

Every morning when you receive the BI email with portal results:
1. ✅ **Detects** the email automatically (from `c00605mgr@chilis.com`)
2. 🖼️ **Extracts** the portal results image from the email
3. 🔍 **OCR Processing** - Reads text from the image using Tesseract
4. 📊 **Parses Metrics** - Extracts key performance indicators:
   - **Sales** (daily sales in dollars)
   - **Labor %** (labor cost percentage)
   - **Guest Satisfaction** (satisfaction score)
   - **Food Cost %** (food cost percentage)
   - **Speed of Service** (service time metric)
5. 💾 **Stores** metrics in `portal_metrics` database table
6. 📋 **Daily Brief** - Automatically includes metrics in your morning digest

## Setup Required

### Step 1: Install Tesseract OCR (Windows)

1. **Download installer:**
   ```
   https://github.com/UB-Mannheim/tesseract/wiki
   ```
   Get: `tesseract-ocr-w64-setup-5.3.x.exe`

2. **Install:**
   - Run the installer
   - **✅ Check "Add to PATH"** during installation
   - Default install location: `C:\Program Files\Tesseract-OCR`

3. **Verify:**
   ```bash
   tesseract --version
   ```
   Should show: `tesseract 5.3.x`

### Step 2: Python Dependencies (Already Installed)
```bash
cd server
.venv\Scripts\pip install pytesseract pillow
```
✅ Already done!

### Step 3: Database (Already Created)
✅ `portal_metrics` table already created in PostgreSQL

## Usage

### Automatic (Recommended)
The Daily Brief (`/daily-digest`) automatically:
- Scans emails from last 24 hours
- Detects BI portal results email
- Parses metrics via OCR
- Includes in digest output

**No manual action needed!** Just run your daily brief as usual.

### Manual Testing
Test with today's BI email:
```bash
curl http://localhost:8002/api/parse-portal-email
```

Test with specific thread:
```bash
curl http://localhost:8002/api/parse-portal-email?thread_id=YOUR_THREAD_ID
```

Response example:
```json
{
  "success": true,
  "thread_id": "abc123",
  "metrics": {
    "sales": 8543.50,
    "labor_percent": 24.5,
    "guest_satisfaction": 87.3,
    "food_cost_percent": 28.2,
    "speed_of_service": 3.5,
    "parsed_at": "2025-11-11T15:30:00-05:00"
  },
  "message": "Portal metrics parsed and stored successfully!"
}
```

## Daily Brief Integration

When you generate your Daily Brief, AUBS will now say:

```
📊 **Yesterday's Portal Results** (from BI email):
   • Sales: $8,543.50
   • Labor: 24.5%
   • Guest Satisfaction: 87.3
   • Food Cost: 28.2%
   • Speed of Service: 3.5
```

## Database Schema

**Table:** `portal_metrics`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `report_date` | Date | Date of the report (unique) |
| `sales` | Integer | Daily sales (stored as cents) |
| `labor_percent` | Integer | Labor % × 10 (e.g., 24.5% = 245) |
| `guest_satisfaction` | Integer | Score × 10 (e.g., 87.3 = 873) |
| `food_cost_percent` | Integer | Food cost % × 10 |
| `speed_of_service` | Integer | Service metric × 10 |
| `raw_ocr_text` | Text | Raw OCR output (for debugging) |
| `email_sender` | String | c00605mgr@chilis.com |
| `email_subject` | String | Email subject line |
| `parsed_at` | DateTime | When OCR parsing occurred |
| `created_at` | DateTime | Record creation time |

## How OCR Parsing Works

### 1. Text Extraction
The parser uses Tesseract OCR to convert the portal image into text:
```
Sales: $8,543.50
Labor %: 24.5%
Guest Satisfaction: 87.3
...
```

### 2. Regex Pattern Matching
Looks for specific patterns in the OCR text:
- **Sales**: `sales?\s*[:\-]?\s*\$?\s*([\d,]+\.?\d*)`
- **Labor**: `labor\s*%?\s*[:\-]?\s*([\d.]+)`
- **Guest Sat**: `guest\s+sat(?:isfaction)?\s*[:\-]?\s*([\d.]+)`
- And more...

### 3. Data Validation
- Converts strings to floats
- Stores as integers (multiplied by 10 for precision)
- Handles missing data gracefully

## Troubleshooting

### "Tesseract not found"
**Problem:** Tesseract OCR not installed or not in PATH

**Solution:**
1. Install from: https://github.com/UB-Mannheim/tesseract/wiki
2. Make sure "Add to PATH" was checked during install
3. Restart terminal/IDE
4. Test: `tesseract --version`

### "No metrics found"
**Problem:** OCR couldn't read the image or keywords not found

**Solution:**
1. Check `portal_metrics` table - look at `raw_ocr_text` column
2. Verify the image quality is good
3. Check if keywords match (e.g., "Sales", "Labor", "Guest Satisfaction")
4. Adjust regex patterns in `portal_parser.py` if needed

### "No BI email found"
**Problem:** BI email not in last 24 hours

**Solution:**
- Verify email sender is exactly `c00605mgr@chilis.com`
- Check if email arrived today
- Manually provide thread_id: `/api/parse-portal-email?thread_id=...`

## Files Created

1. **`services/portal_parser.py`** - Main OCR parsing logic
2. **`models.py`** - Added `PortalMetrics` database model
3. **`app.py`** - Added `/api/parse-portal-email` endpoint
4. **`smart_assistant.py`** - Modified daily digest to include portal metrics

## Example Daily Digest Output

```markdown
Good morning John! Here's your operations brief for Monday, November 11, 2025:

📊 **Yesterday's Portal Results** (from BI email):
   • Sales: $8,543.50
   • Labor: 24.5%
   • Guest Satisfaction: 87.3
   • Food Cost: 28.2%
   • Speed of Service: 3.5

🔴 **URGENT ITEMS**
1. [Your urgent items...]

🟡 **TODAY'S DEADLINES**
...
```

## Next Steps

1. **Install Tesseract OCR** (see Step 1 above)
2. **Test manually:** `curl http://localhost:8002/api/parse-portal-email`
3. **Run Daily Brief** - Metrics will auto-populate!
4. **Check database:** Query `portal_metrics` table to see stored data

---

## Advanced: Customizing Metrics

To add/modify metrics being parsed, edit `portal_parser.py`:

```python
# Add new metric pattern
custom_metric_pattern = r'my_metric\s*[:\-]?\s*([\d.]+)'
match = re.search(custom_metric_pattern, text, re.IGNORECASE)
if match:
    metrics['my_metric'] = float(match.group(1))
```

Then update the database model in `models.py` and run migration.
