"""
Testing utilities for Document Verification System
Quick tests and validation helpers
"""

import json
from document_verification import (
    DocumentVerificationSystem,
    DataNormalizer,
    VerificationEngine,
    DocumentData
)


def test_normalizer():
    """Test data normalization functions"""
    print("=" * 50)
    print("Testing DataNormalizer")
    print("=" * 50)
    
    normalizer = DataNormalizer()
    
    # Test name normalization
    print("\n1. Name Normalization:")
    names = ["  John  Doe  ", "JOHN DOE", "john doe"]
    for name in names:
        normalized = normalizer.normalize_name(name)
        print(f"   '{name}' → '{normalized}'")
    
    # Test date normalization
    print("\n2. Date Normalization:")
    dates = ["15/05/1990", "15-05-1990", "May 15, 1990", "1990-05-15"]
    for date in dates:
        normalized = normalizer.normalize_date(date)
        print(f"   '{date}' → '{normalized}'")
    
    # Test phone normalization
    print("\n3. Phone Normalization:")
    phones = ["+91-987-654-3210", "98765 43210", "(987) 654-3210", "9876543210"]
    for phone in phones:
        normalized = normalizer.normalize_phone(phone)
        print(f"   '{phone}' → '{normalized}'")
    
    # Test Aadhaar normalization
    print("\n4. Aadhaar Normalization:")
    aadhaars = ["1234 5678 9012", "123456789012", "1234-5678-9012"]
    for aadhaar in aadhaars:
        normalized = normalizer.normalize_aadhaar(aadhaar)
        print(f"   '{aadhaar}' → '{normalized}'")
    
    # Test PAN normalization
    print("\n5. PAN Normalization:")
    pans = ["abcde1234f", "ABCDE1234F", "ABCDE 1234 F"]
    for pan in pans:
        normalized = normalizer.normalize_pan(pan)
        print(f"   '{pan}' → '{normalized}'")
    
    print("\n✅ Normalizer tests completed\n")


def test_verification_rules():
    """Test verification engine with sample data"""
    print("=" * 50)
    print("Testing Verification Rules")
    print("=" * 50)
    
    verifier = VerificationEngine()
    
    # Test Case 1: All matching documents
    print("\n📋 Test Case 1: All Documents Match")
    doc1 = DocumentData(
        full_name="John Doe",
        father_name="James Doe",
        date_of_birth="15/05/1990",
        phone_number="9876543210",
        aadhaar_number="123456789012",
        pan_number="ABCDE1234F"
    )
    
    doc2 = DocumentData(
        full_name="John Doe",
        father_name="James Doe",
        date_of_birth="15/05/1990",
        phone_number="9876543210",
        aadhaar_number="123456789012",
        pan_number="ABCDE1234F"
    )
    
    doc3 = DocumentData(
        full_name="John Doe",
        father_name="James Doe",
        date_of_birth="15/05/1990",
        phone_number="9876543210",
        aadhaar_number="123456789012",
        pan_number="ABCDE1234F"
    )
    
    results = verifier.verify_person([doc1, doc2, doc3])
    print_verification_results(results)
    
    # Test Case 2: Mismatching phone numbers
    print("\n📋 Test Case 2: Phone Number Mismatch")
    doc2_mismatch = DocumentData(
        full_name="John Doe",
        father_name="James Doe",
        date_of_birth="15/05/1990",
        phone_number="9876543211",  # Different phone
        aadhaar_number="123456789012",
        pan_number="ABCDE1234F"
    )
    
    results = verifier.verify_person([doc1, doc2_mismatch, doc3])
    print_verification_results(results)
    
    # Test Case 3: Invalid PAN format
    print("\n📋 Test Case 3: Invalid PAN Format")
    doc_invalid_pan = DocumentData(
        full_name="John Doe",
        father_name="James Doe",
        date_of_birth="15/05/1990",
        phone_number="9876543210",
        aadhaar_number="123456789012",
        pan_number="ABC123"  # Invalid format
    )
    
    results = verifier.verify_person([doc_invalid_pan, doc2, doc3])
    print_verification_results(results)
    
    # Test Case 4: Invalid Aadhaar format
    print("\n📋 Test Case 4: Invalid Aadhaar Format")
    doc_invalid_aadhaar = DocumentData(
        full_name="John Doe",
        father_name="James Doe",
        date_of_birth="15/05/1990",
        phone_number="9876543210",
        aadhaar_number="12345",  # Too short
        pan_number="ABCDE1234F"
    )
    
    results = verifier.verify_person([doc_invalid_aadhaar, doc2, doc3])
    print_verification_results(results)
    
    print("\n✅ Verification tests completed\n")


def print_verification_results(results):
    """Pretty print verification results"""
    overall = results.get('overall_status', 'UNKNOWN')
    
    print(f"\n   Overall Status: {overall}")
    print("   " + "-" * 40)
    
    for rule, result in results.items():
        if rule == 'overall_status':
            continue
        
        status = result['status']
        message = result['message']
        emoji = "✅" if status == "PASS" else "❌"
        
        print(f"   {emoji} {rule}: {status}")
        print(f"      {message}")


def test_ocr_and_llm(sample_image_path=None):
    """Test OCR and LLM integration (requires API keys)"""
    print("=" * 50)
    print("Testing OCR + LLM Pipeline")
    print("=" * 50)
    
    if not sample_image_path:
        print("\n⚠️  No sample image provided. Skipping OCR test.")
        print("   Usage: test_ocr_and_llm('path/to/image.jpg')")
        return
    
    try:
        system = DocumentVerificationSystem(
            ocr_provider='azure',
            llm_model='gpt-4'
        )
        
        print(f"\n📄 Processing: {sample_image_path}")
        
        # Extract text
        print("\n1. OCR Extraction...")
        raw_text = system.ocr.extract_text(sample_image_path)
        print(f"   Extracted {len(raw_text)} characters")
        print(f"   Preview: {raw_text[:200]}...")
        
        # Structure with LLM
        print("\n2. LLM Structuring...")
        structured = system.llm.structure_text(raw_text, "Government ID")
        print(f"   Extracted fields:")
        for field, value in structured.__dict__.items():
            if value:
                print(f"   - {field}: {value}")
        
        print("\n✅ OCR + LLM test completed\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("   Make sure API keys are set in .env file")


def validate_output_json(json_file='verification_results.json'):
    """Validate output JSON structure"""
    print("=" * 50)
    print("Validating Output JSON")
    print("=" * 50)
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        print(f"\n✅ JSON is valid")
        print(f"   Total persons processed: {len(data)}")
        
        # Check each person's structure
        required_keys = ['person_id', 'extracted_data', 'verification_results', 'overall_status']
        
        for i, person in enumerate(data):
            person_id = person.get('person_id', f'Person {i+1}')
            
            # Check required keys
            missing_keys = [key for key in required_keys if key not in person]
            if missing_keys:
                print(f"\n⚠️  {person_id}: Missing keys: {missing_keys}")
            else:
                status = person['overall_status']
                emoji = "✅" if status == "VERIFIED" else "❌"
                print(f"   {emoji} {person_id}: {status}")
                
                # Count rules passed/failed
                results = person['verification_results']
                passed = sum(1 for r in results.values() if isinstance(r, dict) and r.get('status') == 'PASS')
                total = sum(1 for r in results.values() if isinstance(r, dict))
                print(f"      Rules: {passed}/{total} passed")
        
        print("\n✅ Validation completed\n")
        
    except FileNotFoundError:
        print(f"\n❌ File not found: {json_file}")
    except json.JSONDecodeError as e:
        print(f"\n❌ Invalid JSON: {str(e)}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


def generate_sample_output():
    """Generate a sample output JSON for reference"""
    print("=" * 50)
    print("Generating Sample Output")
    print("=" * 50)
    
    sample_output = {
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
                "employee_id": None,
                "account_number": None,
                "document_type": "Government ID"
            },
            "document_2": {
                "full_name": "john doe",
                "father_name": None,
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
                "aadhaar_number": None,
                "pan_number": "ABCDE1234F",
                "employee_id": None,
                "account_number": "1234567890",
                "document_type": "Bank Statement"
            },
            "document_3": {
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
                "aadhaar_number": None,
                "pan_number": None,
                "employee_id": "EMP001",
                "account_number": None,
                "document_type": "Employment Letter"
            }
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
                "status": "PASS",
                "message": "Phone numbers match"
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
        "overall_status": "VERIFIED"
    }
    
    output_file = 'sample_output.json'
    with open(output_file, 'w') as f:
        json.dump([sample_output], f, indent=2)
    
    print(f"\n✅ Sample output saved to: {output_file}")
    print("   Use this as a reference for expected output format\n")


if __name__ == '__main__':
    print("\n🧪 Document Verification System - Test Suite\n")
    
    # Run tests
    test_normalizer()
    test_verification_rules()
    
    # Optional: Test OCR + LLM (requires API keys and sample image)
    # test_ocr_and_llm('path/to/sample.jpg')
    
    # Generate sample output
    generate_sample_output()
    
    # Validate existing output (if available)
    # validate_output_json('verification_results.json')
    
    print("=" * 50)
    print("All tests completed! 🎉")
    print("=" * 50)