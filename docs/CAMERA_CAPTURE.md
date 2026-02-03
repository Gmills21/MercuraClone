# Mobile Camera Capture
## Capture RFQs from Photos

---

## Overview

**Camera Capture** allows users to take photos of RFQ emails, documents, or handwritten notes and automatically extract quote data using OCR (Optical Character Recognition).

**Use Cases:**
- Forwarded email screenshots
- Photos of paper RFQs
- Whiteboard/project site photos
- Handwritten notes from meetings

---

## How It Works

```
User Journey:
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   1. CAPTURE    │ →   │  2. PROCESS     │ →   │  3. REVIEW      │
│                 │     │                 │     │                 │
│ • Take photo    │     │ • OCR extracts  │     │ • Review items  │
│ • Or choose     │     │   text          │     │ • Edit if needed│
│   from gallery  │     │ • AI parses     │     │ • Create quote  │
│                 │     │   structure     │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## Technical Flow

### 1. Image Upload
```
Frontend → Backend
POST /image-extract/upload
FormData: { file: image.jpg, source: 'camera' }
```

### 2. OCR Processing
```python
# Tesseract OCR extracts raw text
ocr_text = pytesseract.image_to_string(image)

# Example output:
"From: ACME Corp
Need quote for:
- 25x Industrial Widget
- 10x Heavy Duty Model
Delivery: March 15th"
```

### 3. AI Parsing
```python
# OpenRouter AI parses structured data
{
  "customer_name": "ACME Corp",
  "line_items": [
    {"item_name": "Industrial Widget", "quantity": 25},
    {"item_name": "Heavy Duty Model", "quantity": 10}
  ],
  "delivery_date": "March 15th"
}
```

### 4. Quote Creation
```python
# One-click quote creation
POST /image-extract/create-quote
→ Creates draft quote with extracted items
```

---

## User Interface

### Step 1: Choose Capture Method
```
┌─────────────────────────────────────────────┐
│ Camera Capture                              │
│ Take a photo of an RFQ email or document    │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────┐    ┌─────────────┐        │
│  │   📷        │    │   🖼️        │        │
│  │  Take Photo │    │   Gallery   │        │
│  │             │    │             │        │
│  │ Use camera  │    │ Choose      │        │
│  │ to capture  │    │ existing    │        │
│  └─────────────┘    └─────────────┘        │
│                                             │
│  💡 Tips:                                   │
│  • Make sure text is clearly visible        │
│  • Good lighting helps accuracy             │
│  • Capture full document                    │
│  • Avoid shadows and glare                  │
│                                             │
└─────────────────────────────────────────────┘
```

### Step 2: Processing
```
┌─────────────────────────────────────────────┐
│                                             │
│           ⟳  Analyzing Image...             │
│                                             │
│     We're extracting text and identifying   │
│     items                                   │
│                                             │
│     This usually takes 5-10 seconds         │
│                                             │
└─────────────────────────────────────────────┘
```

### Step 3: Review Results
```
┌─────────────────────────────────────────────┐
│ Review Extraction                           │
│ Confidence: 78%                             │
├─────────────────────────────────────────────┤
│                                             │
│ Customer Information                        │
│ Name: ACME Corp                             │
│ Email: quotes@acme.com                      │
│                                             │
│ Items Found (2)                             │
│ ┌─────────────────────────────────────────┐ │
│ │ Industrial Widget          Qty: 25     │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ Heavy Duty Model           Qty: 10     │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ [View Extracted Text (expandable)]          │
│                                             │
│ [Create Quote from Extraction]              │
│ [Create Quote Manually]                     │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Implementation

### Backend

**File:** `app/image_extraction_service.py`
```python
class ImageExtractionService:
    async def extract_from_image(self, image_data: bytes) -> Dict:
        # 1. Process image (resize, grayscale, enhance)
        # 2. Run Tesseract OCR
        # 3. Parse with AI (OpenRouter)
        # 4. Return structured data
```

**File:** `app/routes/image_extract.py`
```python
@router.post("/upload")
async def upload_image_for_extraction(file: UploadFile):
    # Handle image upload
    # Return extracted data

@router.post("/create-quote")
async def create_quote_from_image(file: UploadFile):
    # Extract + Create quote in one step
```

### Frontend

**File:** `frontend/src/pages/CameraCapture.tsx`
```typescript
// 4-step wizard: Capture → Processing → Review → Creating
// Uses getUserMedia for camera access
// File input fallback for gallery
```

---

## Requirements

### System Dependencies
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows (via installer)
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Python Dependencies
```
Pillow==10.2.0          # Image processing
pytesseract==0.3.10     # OCR wrapper
```

### Browser Support
- ✅ Chrome/Edge (full support)
- ✅ Safari iOS (camera + gallery)
- ✅ Chrome Android (camera + gallery)
- ⚠️ Firefox (gallery only, camera limited)

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/image-extract/upload` | POST | Upload image, get extraction |
| `/image-extract/base64` | POST | Upload base64 image (mobile) |
| `/image-extract/create-quote` | POST | Extract + Create quote |
| `/image-extract/status` | GET | Check service availability |

---

## Tips for Best Results

### Do:
- ✅ Take photos in good lighting
- ✅ Keep camera steady and in focus
- ✅ Capture full document
- ✅ Ensure text is readable size

### Don't:
- ❌ Use blurry images
- ❌ Have shadows over text
- ❌ Capture at extreme angles
- ❌ Use extremely large files (>10MB)

---

## Fallback Behavior

If AI parsing fails:
1. Returns basic OCR text
2. Attempts regex-based extraction
3. User can manually create quote

If OCR fails entirely:
1. Returns error message
2. Suggests trying clearer photo
3. Offers manual quote creation

---

## Future Enhancements

### Phase 2:
- [ ] Multiple image upload (batch processing)
- [ ] Image cropping/rotation before processing
- [ ] Confidence score per field
- [ ] Manual correction UI

### Phase 3:
- [ ] Handwriting recognition improvements
- [ ] Table/invoice detection
- [ ] Barcode/QR code scanning
- [ ] Auto-crop document edges

### Phase 4:
- [ ] Real-time camera preview with overlay
- [ ] Smart focus/exposure hints
- [ ] Multi-page document support
- [ ] Integration with cloud storage (Dropbox, Drive)

---

## The Pitch

> *"Standing at a job site with a paper RFQ? Just take a photo. Whiteboard full of items from a meeting? Snap it. Email forwarded as a screenshot? Capture it. Our camera feature reads the text, extracts the items, and creates a quote - no typing required."*

---

*Camera Capture extends OpenMercura to the physical world, turning any document into a quote in seconds.*
