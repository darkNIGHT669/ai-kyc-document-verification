"""
Image Preprocessing Module
Enhances image quality before OCR for better accuracy
"""

import cv2
import numpy as np
from PIL import Image
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """
    Enhances document images before OCR processing
    Handles: denoising, contrast enhancement, skew correction, binarization
    """
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    
    def preprocess(self, image_path, output_path=None, operations=None):
        """
        Apply preprocessing operations to image
        
        Args:
            image_path: Path to input image
            output_path: Path to save processed image (optional)
            operations: List of operations to apply (default: all)
                       Options: ['denoise', 'enhance_contrast', 'binarize', 'deskew']
        
        Returns:
            Processed image as numpy array
        """
        if operations is None:
            operations = ['denoise', 'enhance_contrast', 'binarize']
        
        logger.info(f"Preprocessing image: {image_path}")
        
        # Load image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Convert to grayscale
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply operations
        for operation in operations:
            if operation == 'denoise':
                img = self.denoise(img)
            elif operation == 'enhance_contrast':
                img = self.enhance_contrast(img)
            elif operation == 'binarize':
                img = self.binarize(img)
            elif operation == 'deskew':
                img = self.deskew(img)
            else:
                logger.warning(f"Unknown operation: {operation}")
        
        # Save if output path provided
        if output_path:
            cv2.imwrite(str(output_path), img)
            logger.info(f"Saved preprocessed image to: {output_path}")
        
        return img
    
    def denoise(self, img):
        """Remove noise from image"""
        logger.debug("Applying denoising")
        
        # Use Non-local Means Denoising
        denoised = cv2.fastNlMeansDenoising(img, None, h=10, templateWindowSize=7, searchWindowSize=21)
        
        return denoised
    
    def enhance_contrast(self, img):
        """Enhance image contrast using CLAHE"""
        logger.debug("Enhancing contrast")
        
        # Create CLAHE object (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(img)
        
        return enhanced
    
    def binarize(self, img):
        """Convert image to binary (black and white)"""
        logger.debug("Binarizing image")
        
        # Use adaptive thresholding for better results with varying lighting
        binary = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    
    def deskew(self, img):
        """Correct image skew/rotation"""
        logger.debug("Deskewing image")
        
        # Detect skew angle
        coords = np.column_stack(np.where(img > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        # Adjust angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        # Rotate image to deskew
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )
        
        return rotated
    
    def remove_borders(self, img, border_size=10):
        """Remove borders from scanned documents"""
        logger.debug("Removing borders")
        
        h, w = img.shape[:2]
        cropped = img[border_size:h-border_size, border_size:w-border_size]
        
        return cropped
    
    def resize_for_ocr(self, img, target_height=2000):
        """Resize image to optimal size for OCR (maintains aspect ratio)"""
        logger.debug(f"Resizing image to height: {target_height}")
        
        h, w = img.shape[:2]
        if h < target_height:
            # Upscale if too small
            scale = target_height / h
            new_w = int(w * scale)
            resized = cv2.resize(img, (new_w, target_height), interpolation=cv2.INTER_CUBIC)
        elif h > target_height * 2:
            # Downscale if too large
            scale = target_height / h
            new_w = int(w * scale)
            resized = cv2.resize(img, (new_w, target_height), interpolation=cv2.INTER_AREA)
        else:
            resized = img
        
        return resized
    
    def preprocess_batch(self, input_dir, output_dir, operations=None):
        """Preprocess all images in a directory"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        processed_count = 0
        
        for img_file in input_path.iterdir():
            if img_file.suffix.lower() in self.supported_formats:
                try:
                    output_file = output_path / img_file.name
                    self.preprocess(img_file, output_file, operations)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to process {img_file}: {str(e)}")
        
        logger.info(f"Preprocessed {processed_count} images")
        return processed_count
    
    def compare_before_after(self, image_path, save_comparison=False):
        """
        Show before/after comparison of preprocessing
        Useful for tuning preprocessing parameters
        """
        original = cv2.imread(str(image_path))
        if len(original.shape) == 3:
            original_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        else:
            original_gray = original
        
        # Apply preprocessing
        processed = self.preprocess(image_path)
        
        if save_comparison:
            # Stack images side by side
            comparison = np.hstack([original_gray, processed])
            output_file = Path(image_path).parent / f"{Path(image_path).stem}_comparison.jpg"
            cv2.imwrite(str(output_file), comparison)
            logger.info(f"Comparison saved to: {output_file}")
        
        return original_gray, processed


def enhance_for_ocr(image_path, output_path=None):
    """
    Quick function to enhance an image for OCR
    
    Args:
        image_path: Path to input image
        output_path: Path to save enhanced image (optional)
    
    Returns:
        Enhanced image path or numpy array
    """
    preprocessor = ImagePreprocessor()
    
    # Apply best practices for OCR
    operations = ['denoise', 'enhance_contrast', 'binarize']
    
    enhanced = preprocessor.preprocess(image_path, output_path, operations)
    
    return output_path if output_path else enhanced


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess document images for OCR')
    parser.add_argument('input', help='Input image or directory')
    parser.add_argument('-o', '--output', help='Output path')
    parser.add_argument('--batch', action='store_true', help='Process directory in batch')
    parser.add_argument('--compare', action='store_true', help='Show before/after comparison')
    parser.add_argument('--operations', nargs='+', 
                       choices=['denoise', 'enhance_contrast', 'binarize', 'deskew'],
                       help='Preprocessing operations to apply')
    
    args = parser.parse_args()
    
    preprocessor = ImagePreprocessor()
    
    if args.batch:
        preprocessor.preprocess_batch(args.input, args.output or './preprocessed', args.operations)
    elif args.compare:
        preprocessor.compare_before_after(args.input, save_comparison=True)
    else:
        preprocessor.preprocess(args.input, args.output, args.operations)
    
    print("✅ Preprocessing completed!")