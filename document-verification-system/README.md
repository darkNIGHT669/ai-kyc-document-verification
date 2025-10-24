# Document Verification System

An intelligent document entity extraction and verification system for KYC workflows, built with OCR and LLM APIs.

## 🎯 Features

- **Multi-Provider OCR Support**: Azure Computer Vision & Google Cloud Vision
- **LLM-Powered Extraction**: Uses GPT-4/Claude to structure OCR text into JSON
- **Smart Normalization**: Handles OCR errors, date formats, phone variations
- **7-Rule Verification**: Comprehensive validation across documents
- **Production-Ready**: Error handling, logging, modular architecture

## 📋 Prerequisites

- Python 3.8+
- API Keys for:
  - Azure Computer Vision (recommended) OR Google Cloud Vision
  - OpenAI GPT-4 OR Anthropic Claude

## 🚀 Installation

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd document-verification-system
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```env
# OCR API (choose one)
AZURE_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_VISION_KEY=your_azure_key

# OR for Google Cloud Vision
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# LLM API (choose one)
OPENAI_API_KEY=your_openai_key

# OR for Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_key
```

### 5. Download Dataset

Download the dataset from the provided Google Drive link and extract to `./dataset/` directory:

```
dataset/
├── P001_doc1.jpg
├── P001_doc2.jpg
├── P001_doc3.jpg
├── P002_doc1.jpg
└── ...
```

## 💻 Usage

### Basic Usage

```python
from document_verification import DocumentVerificationSystem

# Initialize system
system = DocumentVerificationSystem(
    ocr_provider='azure',  # or 'google'
    llm_model='gpt-4'      # or 'claude-3-opus-20240229'
)

# Process entire dataset
results = system.process_dataset(
    dataset_dir='./dataset',
    output_file='verification_results.json'
)
```

### Process Single Person

```python
# Process specific person
result = system.process_person(
    person_id='P001',
    document_paths={
        'document_1': './dataset/P001_doc1.jpg',
        'document_2': './dataset/P001_doc2.jpg',
        'document_3': './dataset/P001_doc3.jpg'
    }
)

print(json.dumps(result, indent=2))
```

### Run from Command Line

```bash
python document_verification.py
```

## 📊 Output Format

The system generates a JSON file with this structure:

```json
{
  "person_id": "P001",
  "extracted_data": {
    "document_1": {
      "full_name": "john doe",
      "father_name": "james doe",
      "date_of_birth": "15/05/1990",
      "address": {
        "house_number": "123",
        "street": "main street",
        "city": "mumbai",
        "state": "maharashtra",
        "pincode": "400001"
      },
      "phone_number": "9876543210",
      "email": "john@example.com",
      "aadhaar_number": "123456789012",
      "pan_number": "ABCDE1234F",
      "employee_id": null,
      "account_number": null,
      "document_type": "Government ID"
    },
    "document_2": { ... },
    "document_3": { ... }
  },
  "verification_results": {
    "rule_1_name_match": {
      "status": "PASS",
      "message": "Names match across all documents"
    },
    "rule_2_dob_match": {
      "status": "PASS",
      "message": "DOB matches across all documents"
    },
    "rule_3_address_match": {
      "status": "PASS",
      "message": "Addresses match"
    },
    "rule_4_phone_match": {
      "status": "FAIL",
      "message": "Phone mismatch: ['9876543210', '9876543211']"
    },
    "rule_5_father_name_match": {
      "status": "PASS",
      "message": "Father's names match"
    },
    "rule_6_pan_format": {
      "status": "PASS",
      "message": "PAN format valid"
    },
    "rule_7_aadhaar_format": {
      "status": "PASS",
      "message": "Aadhaar format valid"
    }
  },
  "overall_status": "FAILED"
}
```

## 🏗️ Architecture

```
┌─────────────────┐
│  Image/PDF      │
│  Documents      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  OCR Layer      │
│  (Azure/Google) │
└────────┬────────┘
         │ Raw Text
         ▼
┌─────────────────┐
│  LLM Layer      │
│  (GPT/Claude)   │
└────────┬────────┘
         │ Structured JSON
         ▼
┌─────────────────┐
│  Normalization  │
│  Layer          │
└────────┬────────┘
         │ Clean Data
         ▼
┌─────────────────┐
│  Verification   │
│  Engine (7 Rules)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  JSON Output    │
└─────────────────┘
```

## 🔧 Key Components

### 1. OCRProcessor
- Extracts text from images using Azure/Google Vision
- Handles multiple image formats (JPG, PNG, PDF)
- Includes error handling and retry logic

### 2. LLMStructurer
- Uses GPT-4 or Claude to structure OCR text
- Applies prompt engineering for accurate extraction
- Handles OCR error correction (O/0, l/1, S/5)

### 3. DataNormalizer
- Standardizes names (lowercase, trim spaces)
- Normalizes dates to DD/MM/YYYY format
- Cleans phone numbers to 10 digits
- Handles address variations
- Validates PAN and Aadhaar formats

### 4. VerificationEngine
Implements 7 validation rules:
- **Rule 1**: Name matching across documents
- **Rule 2**: Date of birth consistency
- **Rule 3**: Address component matching
- **Rule 4**: Phone number verification
- **Rule 5**: Father's name matching
- **Rule 6**: PAN format validation (5 letters + 4 digits + 1 letter)
- **Rule 7**: Aadhaar format validation (12 digits)

### 5. DocumentVerificationSystem
Main orchestrator that:
- Manages the complete pipeline
- Handles batch processing
- Groups documents by person
- Generates final JSON output

## 🎯 Handling Edge Cases

### OCR Error Correction
- **Character confusion**: O↔0, l↔1, S↔5, B↔8
- **Split words**: "John Smith" misread as "J ohn Sm ith"
- **Extra spaces**: "9 8 7 6 5 4 3 2 1 0" → "9876543210"
- **Poor quality scans**: Using LLM context to fix errors

### Date Format Variations
Handles multiple formats:
- `15/05/1990`
- `15-05-1990`
- `May 15, 1990`
- `1990-05-15`

All normalized to: `DD/MM/YYYY`

### Phone Number Variations
Normalizes:
- `+91-987-654-3210` → `9876543210`
- `98765 43210` → `9876543210`
- `(987) 654-3210` → `9876543210`

### Address Matching
- Handles abbreviations: "St" vs "Street", "Rd" vs "Road"
- Case-insensitive comparison
- Focuses on core components: city, state, pincode

## 📈 Performance Tips

### 1. API Rate Limits
- Azure: 10 calls/sec for free tier
- OpenAI: 3500 requests/min for GPT-4
- Implement rate limiting if processing large batches

### 2. Cost Optimization
- Use Azure Read API (optimized for documents)
- Cache OCR results to avoid re-processing
- Use GPT-3.5 for initial testing, GPT-4 for production

### 3. Accuracy Improvements
- Preprocess images: denoise, enhance contrast
- Use higher resolution scans
- Implement retry logic for failed extractions

## 🧪 Testing

### Test with Sample Documents

```python
# Test single document extraction
from document_verification import OCRProcessor, LLMStructurer

ocr = OCRProcessor('azure')
llm = LLMStructurer('gpt-4')

# Extract and structure
text = ocr.extract_text('sample_aadhaar.jpg')
data = llm.structure_text(text, 'Government ID')

print(data)
```

### Test Verification Rules

```python
from document_verification import VerificationEngine, DocumentData

verifier = VerificationEngine()

# Create test documents
doc1 = DocumentData(
    full_name="John Doe",
    date_of_birth="15/05/1990",
    phone_number="9876543210"
)

doc2 = DocumentData(
    full_name="John Doe",
    date_of_birth="15/05/1990",
    phone_number="9876543210"
)

# Verify
results = verifier.verify_person([doc1, doc2])
print(results)
```

## 🐛 Troubleshooting

### Issue: "Azure credentials not found"
**Solution**: Ensure `.env` file has correct Azure keys:
```env
AZURE_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_VISION_KEY=your_key_here
```

### Issue: "Module not found" errors
**Solution**: Install all dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Poor extraction quality
**Solutions**:
1. Check image quality (minimum 300 DPI recommended)
2. Preprocess images (enhance contrast, denoise)
3. Try different OCR provider (Azure vs Google)
4. Adjust LLM prompts for better extraction

### Issue: High API costs
**Solutions**:
1. Cache OCR results
2. Use GPT-3.5-turbo for testing
3. Process in smaller batches
4. Implement error handling to avoid retries

## 📁 Project Structure

```
document-verification-system/
├── document_verification.py    # Main module
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .env                        # Environment variables (create this)
├── .gitignore                  # Git ignore rules
├── dataset/                    # Document images
│   ├── P001_doc1.jpg
│   ├── P001_doc2.jpg
│   └── ...
├── output/
│   └── verification_results.json
└── tests/                      # Unit tests (optional)
    ├── test_ocr.py
    ├── test_verification.py
    └── test_normalization.py
```

## 🔐 Security Best Practices

1. **Never commit API keys**: Use `.env` file (add to `.gitignore`)
2. **Secure document storage**: Encrypt sensitive documents
3. **Data privacy**: Delete processed documents after verification
4. **API key rotation**: Regularly rotate API credentials
5. **Access control**: Limit API key permissions to minimum required

## 🚀 Advanced Features (Optional)

### 1. Image Preprocessing

```python
import cv2
from PIL import Image

def preprocess_image(image_path):
    """Enhance image quality before OCR"""
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    
    return enhanced
```

### 2. Confidence Scores

Track extraction confidence:

```python
def extract_with_confidence(self, image_path):
    """Extract text with confidence scores"""
    # Azure provides confidence scores
    result = self.client.read_in_stream(image_stream, raw=True)
    
    for line in result.analyze_result.read_results[0].lines:
        print(f"Text: {line.text}, Confidence: {line.confidence}")
```

### 3. Parallel Processing

Process multiple persons in parallel:

```python
from concurrent.futures import ThreadPoolExecutor

def process_dataset_parallel(self, dataset_dir, max_workers=4):
    """Process dataset with parallel workers"""
    person_docs = self._group_documents_by_person(dataset_dir)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(self.process_person, pid, docs): pid 
            for pid, docs in person_docs.items()
        }
        
        results = []
        for future in futures:
            results.append(future.result())
    
    return results
```

## 📊 Expected Performance

- **Extraction Time**: 3-5 seconds per document (Azure OCR)
- **LLM Processing**: 2-4 seconds per document (GPT-4)
- **Total per Person**: ~20-30 seconds (3 documents)
- **Accuracy**: 95%+ with good quality scans

## 🎥 Video Walkthrough Guide

When recording your Loom video, cover:

1. **Demo (3 min)**:
   - Show the system processing 2-3 persons
   - Display extracted data for each document
   - Show verification results (both PASS and FAIL cases)

2. **Code Walkthrough (3 min)**:
   - OCR integration (`OCRProcessor` class)
   - LLM structuring (`LLMStructurer` class)
   - Verification logic (`VerificationEngine` class)
   - Normalization functions

3. **Technical Discussion (2 min)**:
   - Architecture decisions (why Azure + GPT-4)
   - Edge case handling (OCR errors, format variations)
   - Challenges faced (character confusion, date parsing)
   - Trade-offs (accuracy vs speed, cost vs quality)

## 📝 Submission Checklist

- [ ] Code works end-to-end
- [ ] All 10 persons processed successfully
- [ ] `verification_results.json` generated
- [ ] `requirements.txt` complete
- [ ] `README.md` with setup instructions
- [ ] `.env.example` file with template
- [ ] GitHub repository public/accessible
- [ ] Loom video recorded (5-8 minutes)
- [ ] Video link is public or unlisted

## 🤝 Support

For questions or issues:
1. Check troubleshooting section
2. Review Azure/OpenAI documentation
3. Check GitHub issues (if applicable)

## 📄 License

This project is for educational/assignment purposes.

---

**Built with ❤️ for Chatzy AI Assignment**