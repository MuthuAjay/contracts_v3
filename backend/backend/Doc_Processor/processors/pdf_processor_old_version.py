import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import fitz
import numpy as np
import cv2
from paddleocr import PaddleOCR
from PIL import Image
import io
import logging
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from queue import Queue
from threading import Lock
from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)

class PDFProcessor(BaseProcessor):
    """
    Enhanced PDF processor with multi-threading support and improved OCR capabilities.
    
    Features:
    - Thread-safe OCR processing
    - Concurrent page processing
    - Enhanced image preprocessing
    - Robust error handling
    - Memory-efficient processing
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.ocr_lock = Lock()
        self.ocr = self._initialize_ocr()
        self.max_workers = config.get('max_workers', min(32, (os.cpu_count() or 1) + 4))
        
    def _initialize_ocr(self) -> PaddleOCR:
        """Initialize PaddleOCR with optimized settings."""
        return PaddleOCR(
            use_angle_cls=True,
            lang=self.config.get('language', 'en'),
            use_gpu=False,
            enable_mkldnn=True,
            show_log=False
        )

    def _validate_config(self) -> None:
        """Validate processor configuration with extended checks."""
        required_keys = ['ocr_enabled', 'language', 'dpi']
        if not all(key in self.config for key in required_keys):
            raise ValueError(f"Missing required config keys: {required_keys}")
        
        # Validate DPI range
        if not 72 <= self.config['dpi'] <= 600:
            raise ValueError("DPI must be between 72 and 600")

    def process(self, file_path: Path) -> Dict[str, Any]:
        """
        Process PDF document with concurrent page processing.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing processed content and metadata
        """
        self._log_processing_status("Started processing", file_path)
        try:
            doc = fitz.open(str(file_path))
            
            # Process pages concurrently
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit page processing tasks
                future_to_page = {
                    executor.submit(self._process_page, page, page_num): page_num
                    for page_num, page in enumerate(doc)
                }
                
                # Process pages and collect results
                pages_content = [None] * len(doc)
                for future in concurrent.futures.as_completed(future_to_page):
                    page_num = future_to_page[future]
                    try:
                        print(f"Processing page {page_num}")
                        pages_content[page_num] = future.result()
                    except Exception as e:
                        logger.error(f"Error processing page {page_num}: {str(e)}")
                        pages_content[page_num] = self._create_error_page_content(page_num, str(e))
            
            # Extract images if enabled
            images = []
            if self.config.get('extract_images', True):
                images = self._extract_images_concurrent(doc)
            
            return {
                'content': pages_content,
                'metadata': self._extract_metadata(doc),
                'extracted_images': images
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            raise

    def _process_page(self, page, page_num: int) -> Dict[str, Any]:
        """
        Process a single PDF page with enhanced OCR capabilities.
        
        Args:
            page: PDF page object
            page_num: Page number
            
        Returns:
            Dictionary containing page content and metadata
        """
        try:
            # Try native text extraction first
            text = page.get_text()
            # print(f"Extracted text: {len(text)}")
            if text.strip():
                return self._create_page_content(text, 'native', page_num, page)
            
            # Perform OCR if enabled and no native text found
            if self.config['ocr_enabled']:
                logging.info(f"Performing OCR on page {page_num}")
                return self._perform_ocr_on_page(page, page_num)
            
            return self._create_page_content('', 'none', page_num, page)
            
        except Exception as e:
            logger.error(f"Error processing page {page_num}: {str(e)}")
            return self._create_error_page_content(page_num, str(e))

    def _perform_ocr_on_page(self, page, page_num: int) -> Dict[str, Any]:
        """
        Perform OCR on a page with enhanced preprocessing and text extraction.
        
        Args:
            page: PDF page object
            page_num: Page number
            
        Returns:
            Dictionary containing OCR results with extracted text
        """
        pix = page.get_pixmap(dpi=self.config['dpi'])
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_np = np.array(img)
        
        # Apply preprocessing
        processed_img = self._preprocess_image(img_np)
        
        # Thread-safe OCR processing
        with self.ocr_lock:
            results = self.ocr.ocr(processed_img)
        
        if not results or not results[0]:
            return self._create_page_content('', 'ocr', page_num, page)
        
        # Extract text and create text blocks
        text_blocks = []
        full_text = []
        
        for line in results[0]:
            text = line[1][0].strip()
            confidence = float(line[1][1])
            
            if text:
                text_blocks.append({
                    'text': text,
                    'confidence': confidence,
                    'bbox': line[0],
                    'page': page_num
                })
                full_text.append(text)
        
        return {
            'text': ' '.join(full_text),
            'text_blocks': text_blocks,
            'source': 'ocr',
            'page': page_num,
            'dimensions': page.rect.round(),
            'rotation': page.rotation,
            'confidence': np.mean([block['confidence'] for block in text_blocks]) if text_blocks else 0.0
        }

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Enhanced image preprocessing pipeline.
        
        Args:
            image: Input image array
            
        Returns:
            Preprocessed image array
        """
        try:
            if image is None:
                raise ValueError("Image is None")
                
            print(f"Image shape: {image.shape}, dtype: {image.dtype}")
            
            # Ensure image is in BGR format if not already
            if len(image.shape) == 2:
                image = image
            elif image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            elif image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

                            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(binary)
            
            # Deskew if enabled
            if self.config.get('enable_deskew', True):
                denoised = self._deskew_image(denoised)
            
            return denoised
            
        except Exception as e:
            logger.error(f"Error in image preprocessing: {str(e)}")
            return image

    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """
        Deskew image using Hough transform.
        
        Args:
            image: Input image array
            
        Returns:
            Deskewed image array
        """
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
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

    def _extract_images_concurrent(self, doc) -> List[Dict[str, Any]]:
        """
        Extract images from PDF concurrently.
        
        Args:
            doc: PDF document object
            
        Returns:
            List of extracted image information
        """
        images_queue = Queue()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for page in doc:
                for img_index, img in enumerate(page.get_images()):
                    futures.append(
                        executor.submit(
                            self._extract_single_image, 
                            doc, page, img, img_index, images_queue
                        )
                    )
            
            # Wait for all tasks to complete
            concurrent.futures.wait(futures)
        
        # Collect results
        images = []
        while not images_queue.empty():
            images.append(images_queue.get())
        
        return sorted(images, key=lambda x: (x['page'], x['index']))

    def _extract_single_image(
        self, 
        doc, 
        page, 
        img, 
        img_index: int, 
        queue: Queue
    ) -> None:
        """
        Extract a single image from PDF and add to queue.
        
        Args:
            doc: PDF document object
            page: PDF page object
            img: Image object
            img_index: Image index
            queue: Queue for storing results
        """
        try:
            xref = img[0]
            base_image = doc.extract_image(xref)
            
            if not base_image:
                return
            
            image_info = self._process_extracted_image(
                base_image, page.number, img_index, xref
            )
            
            if image_info:
                queue.put(image_info)
                
        except Exception as e:
            logger.warning(
                f"Error extracting image {img_index} from page {page.number}: {str(e)}"
            )

    def _process_extracted_image(
        self, 
        base_image: Dict[str, Any], 
        page_num: int, 
        img_index: int,
        xref: int
    ) -> Optional[Dict[str, Any]]:
        """
        Process extracted image and prepare metadata.
        
        Args:
            base_image: Extracted image data
            page_num: Page number
            img_index: Image index
            xref: Image reference
            
        Returns:
            Dictionary containing image information and OCR text
        """
        try:
            img_data = base_image["image"]
            img_ext = base_image["ext"]
            
            # Convert image data to PIL Image for metadata
            pil_image = Image.open(io.BytesIO(img_data))
            
            # Convert PIL Image to numpy array for OCR
            img_np = np.array(pil_image)
            
            # Preprocess image for better OCR results
            processed_img = self._preprocess_image(img_np)
            
            # Perform OCR on the image
            with self.ocr_lock:
                ocr_result = self.ocr.ocr(processed_img)
            
            # Extract text from OCR results
            extracted_text = ""
            if ocr_result and ocr_result[0]:
                extracted_text = " ".join(
                    [line[1][0] for line in ocr_result[0] if line[1][0].strip()]
                )
            
            return {
                'page': page_num,
                'index': img_index,
                'format': img_ext,
                'size': pil_image.size,
                'mode': pil_image.mode,
                'colorspace': base_image.get('colorspace', ''),
                'xref': xref,
                'text': extracted_text,
                'image_path': f'page_{page_num}_image_{img_index}.{img_ext}'
            }
            
        except Exception as e:
            logger.error(f"Error processing extracted image: {str(e)}")
            return None

    def _extract_metadata(self, doc) -> Dict[str, Any]:
        """
        Extract PDF metadata.
        
        Args:
            doc: PDF document object
            
        Returns:
            Dictionary containing PDF metadata
        """
        return {
            'pages': len(doc),
            'format': 'pdf',
            'title': doc.metadata.get('title', ''),
            'author': doc.metadata.get('author', ''),
            'creation_date': doc.metadata.get('creationDate', ''),
            'modification_date': doc.metadata.get('modDate', ''),
            'producer': doc.metadata.get('producer', ''),
            'encrypted': doc.is_encrypted
        }

    def _create_page_content(
        self, 
        text: str, 
        source: str, 
        page_num: int, 
        page
    ) -> Dict[str, Any]:
        """Create standardized page content dictionary."""
        return {
            'text': text,
            'source': source,
            'confidence': 1.0 if source == 'native' else None,
            'page': page_num,
            'dimensions': page.rect.round(),
            'rotation': page.rotation
        }

    def _create_error_page_content(
        self, 
        page_num: int, 
        error: str
    ) -> Dict[str, Any]:
        """Create standardized error content dictionary."""
        return {
            'text': '',
            'error': error,
            'page': page_num
        }