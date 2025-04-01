"""
OCR Utilities for MapleLegends ShopHelper
Uses PaddleOCR for text recognition with CPU-only mode
Optimized for game text with faster inference
"""

import os
import numpy as np
from PIL import Image
import time
from paddleocr import PaddleOCR
import cv2
import sys
import shutil
from pathlib import Path
import requests
import io
import tarfile

class OCRProcessor:
    def __init__(self, use_gpu=False, check_models=True):
        """
        Initialize OCR processor with PaddleOCR
        
        Args:
            use_gpu: Whether to use GPU acceleration (default: False for CPU-only)
            check_models: Whether to check if models exist (default: True)
        """
        # Create models directory if it doesn't exist
        os.makedirs('models', exist_ok=True)
        
        # Model paths
        self.det_model_dir = 'models/det'
        self.rec_model_dir = 'models/rec'
        self.cls_model_dir = 'models/cls'
        
        # Check if models exist
        self.models_exist = self.check_models_exist() if check_models else True
        self.initialization_error = None
        
        if not self.models_exist:
            # Don't initialize PaddleOCR yet - models will be downloaded later
            self.ocr = None
        else:
            # Initialize PaddleOCR with optimized settings for game text
            init_success = self.initialize_paddleocr(use_gpu)
            if not init_success:
                self.ocr = None
                self.initialization_error = "Failed to initialize PaddleOCR. Check console for details."
                print("OCR initialization failed. Models may be incomplete or dependencies missing.")
        
        # Store the last OCR result
        self.last_result = None
        self.last_image = None
    
    def check_models_exist(self):
        """
        Check if the required OCR models exist
        
        Returns:
            bool: True if all required models exist, False otherwise
        """
        # Check for model files in the model directories
        det_path = Path(self.det_model_dir)
        rec_path = Path(self.rec_model_dir)
        
        # Check if the directories exist and contain model files
        det_files = list(det_path.glob('*.pdmodel')) if det_path.exists() else []
        rec_files = list(rec_path.glob('*.pdmodel')) if rec_path.exists() else []
        
        return len(det_files) > 0 and len(rec_files) > 0
    
    def initialize_paddleocr(self, use_gpu=False):
        """
        Initialize the PaddleOCR instance with optimized settings
        
        Args:
            use_gpu: Whether to use GPU acceleration
        """
        try:
            # Check for MKL dependencies on Windows
            if sys.platform == 'win32':
                # Add the paddle directory to the PATH to help find MKL libraries
                paddle_dir = os.path.join(os.path.dirname(sys.executable), 'paddle')
                if os.path.exists(paddle_dir):
                    os.environ['PATH'] = paddle_dir + os.pathsep + os.environ.get('PATH', '')
                
                # Also try to find MKL in the current directory structure
                current_dir = os.path.dirname(os.path.abspath(__file__))
                lib_dirs = [
                    os.path.join(current_dir, 'paddle', 'libs'),
                    os.path.join(current_dir, 'paddle'),
                    os.path.join(current_dir, 'libs'),
                    os.path.join(os.path.dirname(current_dir), 'paddle', 'libs'),
                    os.path.join(os.path.dirname(current_dir), 'libs')
                ]
                
                for lib_dir in lib_dirs:
                    if os.path.exists(lib_dir):
                        os.environ['PATH'] = lib_dir + os.pathsep + os.environ.get('PATH', '')
            
            # Initialize PaddleOCR with optimized settings for game text
            self.ocr = PaddleOCR(
                # Disable angle classifier for faster processing (game text is usually horizontal)
                use_angle_cls=False,
                lang='en',
                use_gpu=use_gpu,
                show_log=True,  # Enable logs to help diagnose issues
                # Use faster detection model
                det_algorithm="DB",  # DB is faster than EAST
                # Optimize detection parameters for game text
                det_db_thresh=0.3,  # Lower threshold for faster detection
                det_db_box_thresh=0.5,  # Lower box threshold
                det_db_unclip_ratio=1.6,  # Adjust for game text
                # Recognition optimization
                rec_batch_num=6,  # Increase batch size for faster processing
                rec_algorithm="CRNN",  # CRNN is faster than other options
                # Set model directory to local path
                det_model_dir=self.det_model_dir,
                rec_model_dir=self.rec_model_dir,
                cls_model_dir=self.cls_model_dir
            )
            return True
        except RuntimeError as e:
            error_msg = str(e)
            print(f"PaddleOCR initialization error: {error_msg}")
            
            # Check for common dependency errors
            if "mklml.dll" in error_msg or "libmklml.so" in error_msg:
                print("MKL dependency error detected. Trying to locate MKL libraries...")
                # This could be expanded with more specific handling
            
            return False
        except Exception as e:
            print(f"Unexpected error initializing PaddleOCR: {str(e)}")
            return False
    
    def download_models(self, callback=None):
        """
        Download the OCR models
        
        Args:
            callback: Optional callback function to update progress
            
        Returns:
            bool: True if models were downloaded successfully, False otherwise
        """
        try:
            if callback:
                callback("Starting PaddleOCR model download...")
            
            # First update the UI to show we're starting
            if callback:
                callback("Initializing download process...")
                callback("Creating model directories...")
            
            # Ensure model directories exist
            os.makedirs(self.det_model_dir, exist_ok=True)
            os.makedirs(self.rec_model_dir, exist_ok=True)
            os.makedirs(self.cls_model_dir, exist_ok=True)
            
            if callback:
                callback("Model directories created successfully.")
                callback("Starting download of detection model...")
            
            # Create the PaddleOCR instance with explicit download=True
            try:
                if callback:
                    callback("Downloading detection model (det_db)...")
                
                # Download detection model
                temp_ocr = PaddleOCR(
                    use_angle_cls=False,
                    lang='en',
                    use_gpu=False,
                    show_log=False,
                    det_model_dir=self.det_model_dir,
                    rec_model_dir=None,  # Don't download rec model yet
                    cls_model_dir=None,  # Don't download cls model yet
                    download_font=False  # Don't download fonts to speed up
                )
                
                if callback:
                    callback("Detection model download completed.")
                    callback("Downloading recognition model (rec_crnn)...")
                
                # Download recognition model
                temp_ocr = PaddleOCR(
                    use_angle_cls=False,
                    lang='en',
                    use_gpu=False,
                    show_log=False,
                    det_model_dir=None,  # Already downloaded
                    rec_model_dir=self.rec_model_dir,
                    cls_model_dir=None,  # Don't download cls model yet
                    download_font=False  # Don't download fonts to speed up
                )
                
                if callback:
                    callback("Recognition model download completed.")
                    callback("Verifying model files...")
                
                # After download, check if models exist
                self.models_exist = self.check_models_exist()
                
                if self.models_exist:
                    # Initialize PaddleOCR with the downloaded models
                    if callback:
                        callback("Models verified successfully. Initializing OCR engine...")
                    
                    self.initialize_paddleocr(use_gpu=False)
                    
                    if callback:
                        callback("PaddleOCR Models downloaded and initialized successfully!")
                    return True
                else:
                    if callback:
                        callback("Model verification failed. Some model files may be missing.")
                    return False
                    
            except Exception as e:
                if callback:
                    callback(f"Error during model download: {str(e)}")
                print(f"Model download error: {str(e)}")
                return False
                
        except Exception as e:
            if callback:
                callback(f"Error initializing download: {str(e)}")
            print(f"Model download initialization error: {str(e)}")
            return False
        
    def preprocess_game_text(self, image):
        """
        Preprocess image specifically for game text to improve OCR speed and accuracy
        
        Args:
            image: PIL Image object
        
        Returns:
            Preprocessed numpy array
        """
        # Convert PIL Image to numpy array if needed
        if isinstance(image, Image.Image):
            img_array = np.array(image)
        else:
            img_array = image
            
        # Convert to grayscale for faster processing
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
            
        # Apply binary thresholding to enhance text
        # This works well for game text which often has high contrast
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Optional: Remove noise
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # Convert back to RGB for PaddleOCR
        processed = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
        
        return processed
        
    def process_image(self, image, preprocess=True):
        """
        Process an image and extract text using OCR
        
        Args:
            image: PIL Image object
            preprocess: Whether to apply game text preprocessing
        
        Returns:
            List of detected text and their confidence scores
        """
        # Check if OCR is initialized
        if not self.ocr:
            return []
            
        # Convert PIL Image to numpy array if needed
        if isinstance(image, Image.Image):
            img_array = np.array(image)
        else:
            img_array = image
            
        # Store the original image for reference
        self.last_image = image
        
        # Apply preprocessing for game text if enabled
        if preprocess:
            try:
                img_array = self.preprocess_game_text(img_array)
            except Exception as e:
                print(f"Preprocessing error: {e}")
                # Fall back to original image if preprocessing fails
                if isinstance(image, Image.Image):
                    img_array = np.array(image)
            
        # Run OCR on the image
        start_time = time.time()
        result = self.ocr.ocr(img_array, cls=False)  # Disable classifier for speed
        end_time = time.time()
        
        # Process the results
        processed_results = []
        
        if result and len(result) > 0 and result[0]:
            for line in result[0]:
                text = line[1][0]  # The recognized text
                confidence = line[1][1]  # Confidence score
                box = line[0]  # Bounding box coordinates
                
                processed_results.append({
                    'text': text,
                    'confidence': confidence,
                    'box': box
                })
        
        # Store the processed results
        self.last_result = {
            'results': processed_results,
            'processing_time': end_time - start_time,
            'timestamp': time.time()
        }
        
        return processed_results
    
    def get_all_text(self):
        """
        Get all detected text from the last OCR result
        
        Returns:
            List of detected text strings
        """
        if not self.last_result:
            return []
            
        return [item['text'] for item in self.last_result['results']]
    
    def get_text_with_confidence(self, min_confidence=0.7):
        """
        Get detected text with confidence above threshold
        
        Args:
            min_confidence: Minimum confidence threshold (0-1)
            
        Returns:
            List of text strings with confidence above threshold
        """
        if not self.last_result:
            return []
            
        return [item['text'] for item in self.last_result['results'] 
                if item['confidence'] >= min_confidence]
    
    def get_processing_stats(self):
        """
        Get statistics about the last OCR processing
        
        Returns:
            Dictionary with processing statistics
        """
        if not self.last_result:
            return {
                'processing_time': 0,
                'text_count': 0,
                'timestamp': None
            }
            
        return {
            'processing_time': self.last_result['processing_time'],
            'text_count': len(self.last_result['results']),
            'timestamp': self.last_result['timestamp']
        }
