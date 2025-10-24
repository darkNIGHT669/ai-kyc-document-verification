"""
Document Verification System
Main module for extracting and verifying document entities
"""

import os
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DocumentData:
    """Structured document data"""
    full_name: Optional[str] = None
    father_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None
    employee_id: Optional[str] = None
    account_number: Optional[str] = None
    document_type: Optional[str] = None


class OCRProcessor:
    """Handles OCR text extraction from documents"""
    
    def __init__(self, api_provider='azure'):
        self.api_provider = api_provider
        self._setup_client()
    
    def _setup_client(self):
        """Initialize OCR client based on provider"""
        if self.api_provider == 'azure':
            from azure.cognitiveservices.vision.computervision import ComputerVisionClient
            from msrest.authentication import CognitiveServicesCredentials
            
            endpoint = os.getenv('AZURE_VISION_ENDPOINT')
            key = os.getenv('AZURE_VISION_KEY')
            
            if not endpoint or not key:
                logger.warning("Azure credentials not found. OCR will be simulated.")
                self.client = None
            else:
                self.client = ComputerVisionClient(
                    endpoint, 
                    CognitiveServicesCredentials(key)
                )
        elif self.api_provider == 'google':
            from google.cloud import vision
            self.client = vision.ImageAnnotatorClient()
    
    def extract_text(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            if self.client is None:
                # Fallback: simulate OCR for testing
                logger.info(f"Simulating OCR for {image_path}")
                return self._simulate_ocr(image_path)
            
            if self.api_provider == 'azure':
                return self._extract_azure(image_path)
            elif self.api_provider == 'google':
                return self._extract_google(image_path)
        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {str(e)}")
            raise
    
    def _extract_azure(self, image_path: str) -> str:
        """Extract text using Azure Computer Vision"""
        with open(image_path, 'rb') as image_stream:
            # Use Read API for better text extraction
            read_result = self.client.read_in_stream(image_stream, raw=True)
            operation_id = read_result.headers['Operation-Location'].split('/')[-1]
            
            # Wait for operation to complete
            import time
            while True:
                result = self.client.get_read_result(operation_id)
                if result.status not in ['notStarted', 'running']:
                    break
                time.sleep(1)
            
            # Extract text
            text_lines = []
            if result.status == 'succeeded':
                for page in result.analyze_result.read_results:
                    for line in page.lines:
                        text_lines.append(line.text)
            
            return '\n'.join(text_lines)
    
    def _extract_google(self, image_path: str) -> str:
        """Extract text using Google Vision API"""
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = self.client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(response.error.message)
        
        return response.full_text_annotation.text if response.text_annotations else ""
    
    def _simulate_ocr(self, image_path: str) -> str:
        """Simulate OCR output for testing"""
        # This would be replaced with actual OCR in production
        return f"Simulated OCR text from {os.path.basename(image_path)}"


class LLMStructurer:
    """Uses LLM to structure extracted text into JSON"""
    
    def __init__(self, model='gpt-4'):
        self.model = model
        self._setup_client()
    
    def _setup_client(self):
        """Initialize LLM client"""
        if self.model.startswith('gpt'):
            import openai
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.client = openai
        elif self.model.startswith('claude'):
            import anthropic
            self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def structure_text(self, raw_text: str, document_type: str) -> DocumentData:
        """Convert raw OCR text to structured data"""
        try:
            prompt = self._build_extraction_prompt(raw_text, document_type)
            
            if self.model.startswith('gpt'):
                response = self._call_openai(prompt)
            elif self.model.startswith('claude'):
                response = self._call_claude(prompt)
            
            return self._parse_response(response, document_type)
        
        except Exception as e:
            logger.error(f"LLM structuring failed: {str(e)}")
            raise
    
    def _build_extraction_prompt(self, text: str, doc_type: str) -> str:
        """Build prompt for entity extraction"""
        return f"""Extract structured information from this {doc_type} document.

Raw OCR Text:
{text}

Extract the following fields (use null if not found):
- full_name: Person's complete name
- father_name: Father's name (if present)
- date_of_birth: Date of birth in DD/MM/YYYY format
- address: Dict with house_number, street, city, state, pincode
- phone_number: 10-digit phone number
- email: Email address
- aadhaar_number: 12-digit Aadhaar number
- pan_number: PAN in format ABCDE1234F
- employee_id: Employee ID (for employment letters)
- account_number: Bank account number (for bank statements)

Handle OCR errors:
- Fix common misreads: O/0, l/1, S/5, B/8
- Normalize phone numbers to 10 digits
- Standardize date formats
- Clean address formatting

Return ONLY valid JSON matching this structure:
{{
    "full_name": "string or null",
    "father_name": "string or null",
    "date_of_birth": "DD/MM/YYYY or null",
    "address": {{"house_number": "", "street": "", "city": "", "state": "", "pincode": ""}} or null,
    "phone_number": "string or null",
    "email": "string or null",
    "aadhaar_number": "string or null",
    "pan_number": "string or null",
    "employee_id": "string or null",
    "account_number": "string or null"
}}"""
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        response = self.client.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a document data extraction expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        return response.choices[0].message.content
    
    def _call_claude(self, prompt: str) -> str:
        """Call Claude API"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    def _parse_response(self, response: str, doc_type: str) -> DocumentData:
        """Parse LLM response into DocumentData"""
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response.strip()
        
        data = json.loads(json_str)
        data['document_type'] = doc_type
        
        return DocumentData(**data)


class DataNormalizer:
    """Normalizes and cleans extracted data"""
    
    @staticmethod
    def normalize_name(name: Optional[str]) -> Optional[str]:
        """Normalize name: lowercase, remove extra spaces"""
        if not name:
            return None
        return ' '.join(name.lower().strip().split())
    
    @staticmethod
    def normalize_date(date_str: Optional[str]) -> Optional[str]:
        """Normalize date to DD/MM/YYYY format"""
        if not date_str:
            return None
        
        # Common date patterns
        patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})'        # Month DD, YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if len(match.groups()) == 3:
                        if match.group(1).isalpha():  # Month name format
                            date_obj = datetime.strptime(
                                f"{match.group(1)} {match.group(2)} {match.group(3)}", 
                                "%B %d %Y"
                            )
                        else:
                            day, month, year = match.groups()
                            date_obj = datetime(int(year), int(month), int(day))
                        return date_obj.strftime("%d/%m/%Y")
                except:
                    continue
        
        return date_str
    
    @staticmethod
    def normalize_phone(phone: Optional[str]) -> Optional[str]:
        """Normalize phone to 10 digits"""
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Remove country code if present
        if len(digits) > 10:
            digits = digits[-10:]
        
        return digits if len(digits) == 10 else None
    
    @staticmethod
    def normalize_address(address: Optional[Dict]) -> Optional[Dict]:
        """Normalize address components"""
        if not address:
            return None
        
        normalized = {}
        for key, value in address.items():
            if value:
                normalized[key] = ' '.join(str(value).lower().strip().split())
        
        return normalized if normalized else None
    
    @staticmethod
    def normalize_aadhaar(aadhaar: Optional[str]) -> Optional[str]:
        """Normalize Aadhaar to 12 digits"""
        if not aadhaar:
            return None
        
        digits = re.sub(r'\D', '', aadhaar)
        return digits if len(digits) == 12 else None
    
    @staticmethod
    def normalize_pan(pan: Optional[str]) -> Optional[str]:
        """Normalize PAN format"""
        if not pan:
            return None
        
        pan = pan.upper().replace(' ', '')
        return pan if len(pan) == 10 else None


class VerificationEngine:
    """Implements 7 verification rules"""
    
    def __init__(self):
        self.normalizer = DataNormalizer()
    
    def verify_person(self, documents: List[DocumentData]) -> Dict:
        """Run all verification rules on a person's documents"""
        results = {
            'rule_1_name_match': self._verify_name_match(documents),
            'rule_2_dob_match': self._verify_dob_match(documents),
            'rule_3_address_match': self._verify_address_match(documents),
            'rule_4_phone_match': self._verify_phone_match(documents),
            'rule_5_father_name_match': self._verify_father_name_match(documents),
            'rule_6_pan_format': self._verify_pan_format(documents),
            'rule_7_aadhaar_format': self._verify_aadhaar_format(documents)
        }
        
        # Determine overall status
        all_passed = all(r['status'] == 'PASS' for r in results.values())
        results['overall_status'] = 'VERIFIED' if all_passed else 'FAILED'
        
        return results
    
    def _verify_name_match(self, documents: List[DocumentData]) -> Dict:
        """Rule 1: Verify name matches across documents"""
        names = [self.normalizer.normalize_name(d.full_name) for d in documents if d.full_name]
        
        if len(set(names)) <= 1:
            return {'status': 'PASS', 'message': 'Names match across all documents'}
        else:
            return {'status': 'FAIL', 'message': f'Name mismatch: {names}'}
    
    def _verify_dob_match(self, documents: List[DocumentData]) -> Dict:
        """Rule 2: Verify DOB matches"""
        dobs = [self.normalizer.normalize_date(d.date_of_birth) for d in documents if d.date_of_birth]
        
        if len(set(dobs)) <= 1:
            return {'status': 'PASS', 'message': 'DOB matches across all documents'}
        else:
            return {'status': 'FAIL', 'message': f'DOB mismatch: {dobs}'}
    
    def _verify_address_match(self, documents: List[DocumentData]) -> Dict:
        """Rule 3: Verify address matches"""
        addresses = [self.normalizer.normalize_address(d.address) for d in documents if d.address]
        
        if not addresses:
            return {'status': 'PASS', 'message': 'No addresses to compare'}
        
        # Compare core components: city, state, pincode
        core_components = []
        for addr in addresses:
            if addr:
                core = f"{addr.get('city', '')}_{addr.get('state', '')}_{addr.get('pincode', '')}"
                core_components.append(core)
        
        if len(set(core_components)) <= 1:
            return {'status': 'PASS', 'message': 'Addresses match'}
        else:
            return {'status': 'FAIL', 'message': f'Address mismatch'}
    
    def _verify_phone_match(self, documents: List[DocumentData]) -> Dict:
        """Rule 4: Verify phone numbers match"""
        phones = [self.normalizer.normalize_phone(d.phone_number) for d in documents if d.phone_number]
        
        if len(set(phones)) <= 1:
            return {'status': 'PASS', 'message': 'Phone numbers match'}
        else:
            return {'status': 'FAIL', 'message': f'Phone mismatch: {phones}'}
    
    def _verify_father_name_match(self, documents: List[DocumentData]) -> Dict:
        """Rule 5: Verify father's name matches"""
        father_names = [self.normalizer.normalize_name(d.father_name) for d in documents if d.father_name]
        
        if len(set(father_names)) <= 1:
            return {'status': 'PASS', 'message': "Father's names match"}
        else:
            return {'status': 'FAIL', 'message': f"Father's name mismatch: {father_names}"}
    
    def _verify_pan_format(self, documents: List[DocumentData]) -> Dict:
        """Rule 6: Verify PAN format"""
        pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
        
        for doc in documents:
            if doc.pan_number:
                pan = self.normalizer.normalize_pan(doc.pan_number)
                if pan and not re.match(pan_pattern, pan):
                    return {'status': 'FAIL', 'message': f'Invalid PAN format: {pan}'}
        
        return {'status': 'PASS', 'message': 'PAN format valid'}
    
    def _verify_aadhaar_format(self, documents: List[DocumentData]) -> Dict:
        """Rule 7: Verify Aadhaar format"""
        for doc in documents:
            if doc.aadhaar_number:
                aadhaar = self.normalizer.normalize_aadhaar(doc.aadhaar_number)
                if not aadhaar or len(aadhaar) != 12:
                    return {'status': 'FAIL', 'message': f'Invalid Aadhaar format'}
        
        return {'status': 'PASS', 'message': 'Aadhaar format valid'}


class DocumentVerificationSystem:
    """Main system orchestrator"""
    
    def __init__(self, ocr_provider='azure', llm_model='gpt-4'):
        self.ocr = OCRProcessor(ocr_provider)
        self.llm = LLMStructurer(llm_model)
        self.verifier = VerificationEngine()
    
    def process_person(self, person_id: str, document_paths: Dict[str, str]) -> Dict:
        """Process all documents for a person and verify"""
        logger.info(f"Processing person: {person_id}")
        
        # Extract data from all documents
        extracted_data = {}
        document_objects = []
        
        for doc_name, doc_path in document_paths.items():
            logger.info(f"Processing document: {doc_name}")
            
            # OCR extraction
            raw_text = self.ocr.extract_text(doc_path)
            
            # LLM structuring
            doc_type = self._infer_document_type(doc_name)
            structured_data = self.llm.structure_text(raw_text, doc_type)
            
            extracted_data[doc_name] = asdict(structured_data)
            document_objects.append(structured_data)
        
        # Run verification
        verification_results = self.verifier.verify_person(document_objects)
        
        # Build output
        output = {
            'person_id': person_id,
            'extracted_data': extracted_data,
            'verification_results': verification_results,
            'overall_status': verification_results.pop('overall_status')
        }
        
        return output
    
    def _infer_document_type(self, filename: str) -> str:
        """Infer document type from filename"""
        filename_lower = filename.lower()
        if 'aadhaar' in filename_lower or 'govt' in filename_lower or 'id' in filename_lower:
            return 'Government ID'
        elif 'bank' in filename_lower or 'statement' in filename_lower:
            return 'Bank Statement'
        elif 'employment' in filename_lower or 'letter' in filename_lower or 'employee' in filename_lower:
            return 'Employment Letter'
        return 'Unknown'
    
    def process_dataset(self, dataset_dir: str, output_file: str = 'verification_results.json'):
        """Process entire dataset"""
        dataset_path = Path(dataset_dir)
        all_results = []
        
        # Group documents by person
        person_docs = self._group_documents_by_person(dataset_path)
        
        for person_id, doc_paths in person_docs.items():
            try:
                result = self.process_person(person_id, doc_paths)
                all_results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {person_id}: {str(e)}")
                continue
        
        # Save results
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        return all_results
    
    def _group_documents_by_person(self, dataset_path: Path) -> Dict[str, Dict[str, str]]:
        """Group document files by person ID"""
        person_docs = {}
        
        for file_path in dataset_path.glob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.pdf']:
                # Extract person ID from filename (assuming format: P001_doc1.jpg)
                filename = file_path.stem
                person_id = filename.split('_')[0] if '_' in filename else filename[:4]
                
                if person_id not in person_docs:
                    person_docs[person_id] = {}
                
                doc_key = f"document_{len(person_docs[person_id]) + 1}"
                person_docs[person_id][doc_key] = str(file_path)
        
        return person_docs


if __name__ == '__main__':
    # Example usage
    system = DocumentVerificationSystem(
        ocr_provider='azure',  # or 'google'
        llm_model='gpt-4'      # or 'claude-3-opus-20240229'
    )
    
    # Process dataset
    results = system.process_dataset(
        dataset_dir='./dataset',
        output_file='verification_results.json'
    )
    
    print(f"Processed {len(results)} persons")
    print(f"Results saved to verification_results.json")