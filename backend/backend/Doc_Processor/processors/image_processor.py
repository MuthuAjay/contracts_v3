from pathlib import Path
from typing import Dict, Any
import cv2
import numpy as np
from paddleocr import PaddleOCR
from .base_processor import BaseProcessor

class ImageProcessor(BaseProcessor):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=self.config.get('ocr_language', 'en'),
            show_log=False
        )
    
    def _validate_config(self) -> None:
        required_keys = ['preprocessing_steps', 'ocr_language']
        if not all(key in self.config for key in required_keys):
            raise ValueError(f"Missing required config keys: {required_keys}")
    
    def process(self, file_path: Path) -> Dict[str, Any]:
        self._log_processing_status("Started processing", file_path)
        try:
            image = cv2.imread(str(file_path))
            if image is None:
                raise ValueError(f"Failed to load image: {file_path}")
            
            if self.config['preprocessing_steps']:
                image = self._preprocess_image(image)
            
            results = self.ocr.ocr(image)
            
            text_results = []
            for line in results[0]:
                text_results.append({
                    'text': line[1][0],
                    'confidence': float(line[1][1]),
                    'bbox': line[0]
                })
            
            return {
                'content': [item['text'] for item in text_results],
                'details': text_results,
                'metadata': {
                    'format': 'image',
                    'dimensions': image.shape[:2],
                    'channels': image.shape[2]
                }
            }
            
        except Exception as e:
            self._log_processing_status(f"Error: {str(e)}", file_path)
            raise
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        for step in self.config['preprocessing_steps']:
            if step == 'denoise':
                image = cv2.fastNlMeansDenoisingColored(image)
            elif step == 'deskew':
                image = self._deskew(image)
            elif step == 'contrast':
                image = self._enhance_contrast(image)
        return image
    
    def _deskew(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
        
        if lines is not None:
            angle = np.median([line[0][1] for line in lines]) * 180/np.pi
            if angle > 45:
                angle -= 90
            elif angle < -45:
                angle += 90
            
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC)
        return image
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        lab = cv2.merge((l,a,b))
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)