#!/usr/bin/env python3
"""
Document Verification System - Main Execution Script
Run this script to process the entire dataset
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import main system
from document_verification import DocumentVerificationSystem
from image_preprocessing import ImagePreprocessor

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if required environment variables are set"""
    logger.info("Checking environment configuration...")
    
    issues = []
    
    # Check OCR API
    has_azure = os.getenv('AZURE_VISION_ENDPOINT') and os.getenv('AZURE_VISION_KEY')
    has_google = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not has_azure and not has_google:
        issues.append("❌ No OCR API configured (Azure or Google)")
    else:
        if has_azure:
            logger.info("✅ Azure Computer Vision configured")
        if has_google:
            logger.info("✅ Google Cloud Vision configured")
    
    # Check LLM API
    has_openai = os.getenv('OPENAI_API_KEY')
    has_anthropic = os.getenv('ANTHROPIC_API_KEY')
    
    if not has_openai and not has_anthropic:
        issues.append("❌ No LLM API configured (OpenAI or Anthropic)")
    else:
        if has_openai:
            logger.info("✅ OpenAI API configured")
        if has_anthropic:
            logger.info("✅ Anthropic API configured")
    
    if issues:
        logger.error("Environment check failed:")
        for issue in issues:
            logger.error(f"  {issue}")
        logger.error("\nPlease set required API keys in .env file")
        logger.error("See .env.example for template")
        return False
    
    logger.info("✅ Environment check passed")
    return True


def check_dataset(dataset_dir):
    """Check if dataset exists and has valid structure"""
    logger.info(f"Checking dataset directory: {dataset_dir}")
    
    dataset_path = Path(dataset_dir)
    
    if not dataset_path.exists():
        logger.error(f"❌ Dataset directory not found: {dataset_dir}")
        logger.error("Please download and extract the dataset")
        return False
    
    # Count image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    image_files = [f for f in dataset_path.iterdir() 
                   if f.is_file() and f.suffix.lower() in image_extensions]
    
    if not image_files:
        logger.error(f"❌ No image files found in {dataset_dir}")
        return False
    
    logger.info(f"✅ Found {len(image_files)} document images")
    
    # Estimate number of persons (assuming 3 docs per person)
    estimated_persons = len(image_files) // 3
    logger.info(f"   Estimated persons: {estimated_persons}")
    
    return True


def preprocess_dataset(input_dir, output_dir):
    """Preprocess all images in dataset"""
    logger.info("Starting image preprocessing...")
    
    preprocessor = ImagePreprocessor()
    count = preprocessor.preprocess_batch(
        input_dir, 
        output_dir,
        operations=['denoise', 'enhance_contrast']
    )
    
    logger.info(f"✅ Preprocessed {count} images")
    return output_dir


def process_dataset(dataset_dir, output_file, ocr_provider, llm_model, preprocess):
    """Main processing function"""
    logger.info("=" * 60)
    logger.info("DOCUMENT VERIFICATION SYSTEM")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    
    # Preprocess images if requested
    if preprocess:
        preprocessed_dir = Path(dataset_dir).parent / 'preprocessed'
        dataset_dir = preprocess_dataset(dataset_dir, preprocessed_dir)
    
    # Initialize system
    logger.info(f"\nInitializing system...")
    logger.info(f"  OCR Provider: {ocr_provider}")
    logger.info(f"  LLM Model: {llm_model}")
    
    system = DocumentVerificationSystem(
        ocr_provider=ocr_provider,
        llm_model=llm_model
    )
    
    # Process dataset
    logger.info(f"\nProcessing dataset: {dataset_dir}")
    results = system.process_dataset(dataset_dir, output_file)
    
    # Calculate statistics
    total_persons = len(results)
    verified_count = sum(1 for r in results if r['overall_status'] == 'VERIFIED')
    failed_count = total_persons - verified_count
    
    # Processing time
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("PROCESSING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"\n📊 Summary:")
    logger.info(f"   Total Persons: {total_persons}")
    logger.info(f"   ✅ Verified: {verified_count} ({verified_count/total_persons*100:.1f}%)")
    logger.info(f"   ❌ Failed: {failed_count} ({failed_count/total_persons*100:.1f}%)")
    logger.info(f"   ⏱️  Processing Time: {duration:.2f} seconds")
    logger.info(f"   ⚡ Average per Person: {duration/total_persons:.2f} seconds")
    logger.info(f"\n💾 Results saved to: {output_file}")
    
    # Print verification details
    logger.info("\n📋 Detailed Results:")
    for result in results:
        person_id = result['person_id']
        status = result['overall_status']
        emoji = "✅" if status == "VERIFIED" else "❌"
        
        logger.info(f"\n   {emoji} {person_id}: {status}")
        
        # Show failed rules
        if status == "FAILED":
            for rule, details in result['verification_results'].items():
                if details.get('status') == 'FAIL':
                    logger.info(f"      ❌ {rule}: {details.get('message', 'Failed')}")
    
    return results


def generate_report(results, output_file='report.txt'):
    """Generate a detailed text report"""
    with open(output_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("DOCUMENT VERIFICATION SYSTEM - DETAILED REPORT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Persons Processed: {len(results)}\n\n")
        
        for result in results:
            f.write("-" * 70 + "\n")
            f.write(f"Person ID: {result['person_id']}\n")
            f.write(f"Overall Status: {result['overall_status']}\n")
            f.write("-" * 70 + "\n\n")
            
            # Extracted data summary
            f.write("Extracted Data:\n")
            for doc_name, doc_data in result['extracted_data'].items():
                f.write(f"\n  {doc_name}:\n")
                f.write(f"    Type: {doc_data.get('document_type', 'Unknown')}\n")
                f.write(f"    Name: {doc_data.get('full_name', 'N/A')}\n")
                f.write(f"    DOB: {doc_data.get('date_of_birth', 'N/A')}\n")
                f.write(f"    Phone: {doc_data.get('phone_number', 'N/A')}\n")
            
            # Verification results
            f.write("\n\nVerification Results:\n")
            for rule, details in result['verification_results'].items():
                status = details.get('status', 'UNKNOWN')
                message = details.get('message', 'No message')
                f.write(f"  {rule}: {status}\n")
                f.write(f"    → {message}\n")
            
            f.write("\n\n")
    
    logger.info(f"📄 Detailed report saved to: {output_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Document Verification System - Process and verify KYC documents'
    )
    
    parser.add_argument(
        '--dataset-dir',
        default='./dataset',
        help='Path to dataset directory (default: ./dataset)'
    )
    
    parser.add_argument(
        '--output',
        default='verification_results.json',
        help='Output JSON file (default: verification_results.json)'
    )
    
    parser.add_argument(
        '--ocr-provider',
        choices=['azure', 'google'],
        default='azure',
        help='OCR provider to use (default: azure)'
    )
    
    parser.add_argument(
        '--llm-model',
        choices=['gpt-4', 'gpt-3.5-turbo', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229'],
        default='gpt-4',
        help='LLM model to use (default: gpt-4)'
    )
    
    parser.add_argument(
        '--preprocess',
        action='store_true',
        help='Preprocess images before OCR'
    )
    
    parser.add_argument(
        '--generate-report',
        action='store_true',
        help='Generate detailed text report'
    )
    
    parser.add_argument(
        '--skip-checks',
        action='store_true',
        help='Skip environment and dataset checks'
    )
    
    args = parser.parse_args()
    
    # Run checks
    if not args.skip_checks:
        if not check_environment():
            sys.exit(1)
        
        if not check_dataset(args.dataset_dir):
            sys.exit(1)
    
    # Process dataset
    try:
        results = process_dataset(
            dataset_dir=args.dataset_dir,
            output_file=args.output,
            ocr_provider=args.ocr_provider,
            llm_model=args.llm_model,
            preprocess=args.preprocess
        )
        
        # Generate report if requested
        if args.generate_report:
            report_file = args.output.replace('.json', '_report.txt')
            generate_report(results, report_file)
        
        logger.info("\n🎉 All processing completed successfully!\n")
        
    except Exception as e:
        logger.error(f"\n❌ Processing failed: {str(e)}")
        logger.exception("Full traceback:")
        sys.exit(1)


if __name__ == '__main__':
    main()