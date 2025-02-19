import gc
import os
from pathlib import Path
import torch
from typing import Dict, Any, List, Optional
import fitz
import numpy as np
import cv2
from paddleocr import PaddleOCR
from PIL import Image
import io
import logging
from .base_processor import BaseProcessor
from tqdm.auto import tqdm

import warnings
warnings.filterwarnings("ignore")

print("Torch CUDA available: ", torch.cuda.is_available())

logger = logging.getLogger(__name__)


class PDFProcessor(BaseProcessor):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.ocr = self._initialize_ocr()
        self.max_workers = min(32, (os.cpu_count() or 1) + 4)
        self.chunk_size = config.get("chunk_size", 10)  # Process pages in chunks
        self.save_processed_files = config.get("save_processed_files", True)
        self.save_processed_files_dir = config.get("save_processed_files_dir", "processed_files")

    def _initialize_ocr(self) -> PaddleOCR:
        return PaddleOCR(
            use_angle_cls=True,
            lang=self.config.get("language", "en"),
            use_gpu= True,
            enable_mkldnn=True,
            show_log=False,
        )

    def _validate_config(self) -> None:
        """Validate processor configuration with extended checks."""
        required_keys = ["ocr_enabled", "language", "dpi"]
        if not all(key in self.config for key in required_keys):
            raise ValueError(f"Missing required config keys: {required_keys}")

        # Validate DPI range
        if not 72 <= self.config["dpi"] <= 600:
            raise ValueError("DPI must be between 72 and 600")

    def process(self, file_path: Path) -> Dict[str, Any]:
        try:
            print("Processing PDF file:", file_path)
            logger.info(f"Processing PDF file: {file_path}")
            doc = fitz.open(str(file_path))
            total_pages = len(doc)
            pages_content = []

            for page_num in tqdm(range(total_pages)):
                try:
                    result = self._process_page(doc[page_num], page_num)
                    pages_content.append(result)
                    gc.collect()
                except Exception as e:
                    logger.error(f"Page {page_num} failed: {str(e)}")
                    pages_content.append(self._create_error_page(page_num, str(e)))
            
            # self._save_content({"content": pages_content}, self.save_processed_files_dir, file_path.stem)
            
            with open(f"/home/ajay/contracts_v2/ext.txt", "w") as f:
                for page in pages_content:
                    f.write(page["text"])
                    f.write("\n\n")

            return {"content": pages_content, "metadata": self._get_metadata(doc)}
        finally:
            if "doc" in locals():
                doc.close()
                gc.collect()
                
    # def _save_content(self, content: Dict[str, Any], output_dir: Path, file_name: Any) -> None:
    #     # save the text into a text file
    #     if isinstance(output_dir, str):
    #         output_dir = Path(output_dir)
    #     text_file = output_dir / f"{file_name}.txt"
    #     logger.info(f"Saving text to: {text_file}")
    #     with open(text_file, "w") as f:
    #         for page in content["content"]:
    #             f.write(page["text"])
    #             f.write("\n\n")
    #     print(f"Text saved to: {text_file}")
        

    def _process_page(self, page, page_num: int) -> Dict[str, Any]:
        text = page.get_text().strip()
        if text:
            return self._create_page_content(text, "native", page_num, page)

        if not self.config.get("ocr_enabled"):
            return self._create_page_content("", "none", page_num, page)

        return self._perform_ocr(page, page_num)

    def _perform_ocr(self, page, page_num: int) -> Dict[str, Any]:
        try:
            pix = page.get_pixmap(dpi=self.config.get("dpi", 300))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_np = np.array(img)
            processed_img = self._preprocess_image(img_np)

            results = self.ocr.ocr(processed_img)
            del pix, img, img_np, processed_img

            if not results or not results[0]:
                return self._create_page_content("", "ocr", page_num, page)

            text_blocks = []
            full_text = []
            for line in results[0]:
                if line[1][0].strip():
                    text = '\n' + line[1][0].strip()
                    
                    
                    text_blocks.append(
                        {
                            "text": line[1][0],
                            "confidence": float(line[1][1]),
                            "bbox": line[0],
                            "page": page_num,
                        }
                    )
                    full_text.append(text)

            return {
                "text": " ".join(full_text),
                "text_blocks": text_blocks,
                "source": "ocr",
                "page": page_num,
                "dimensions": page.rect.round(),
                "confidence": (
                    np.mean([b["confidence"] for b in text_blocks])
                    if text_blocks
                    else 0
                ),
            }
        except Exception as e:
            logger.error(f"OCR failed for page {page_num}: {str(e)}")
            return self._create_error_page(page_num, str(e))
        finally:
            gc.collect()

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        try:
            if image is None:
                raise ValueError("Invalid image")

            if len(image.shape) == 2:
                processed = image
            else:
                processed = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

            processed = cv2.adaptiveThreshold(
                processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            processed = cv2.fastNlMeansDenoising(processed)

            if self.config.get("enable_deskew"):
                processed = self._deskew(processed)

            return processed

        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return (
                cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                if len(image.shape) > 2
                else image
            )

    def _deskew(self, image: np.ndarray) -> np.ndarray:
        try:
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)

            if lines is None:
                return image

            angle = np.median([line[0][1] for line in lines]) * 180 / np.pi
            if abs(angle) > 45:
                angle = angle - 90 if angle > 0 else angle + 90

            h, w = image.shape[:2]
            M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1)
            return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC)

        except Exception as e:
            logger.error(f"Deskew failed: {e}")
            return image

    def _extract_images(self, doc) -> List[Dict[str, Any]]:
        images = []
        try:
            for page_num, page in enumerate(doc):
                for img_index, img in enumerate(page.get_images()):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        if not base_image:
                            continue

                        image_info = self._process_image(
                            base_image, page_num, img_index, xref
                        )
                        if image_info:
                            images.append(image_info)

                    except Exception as e:
                        logger.warning(
                            f"Image extraction failed on page {page_num}: {e}"
                        )

            return sorted(images, key=lambda x: (x["page"], x["index"]))

        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            return []

    def _process_image(
        self, base_image: Dict[str, Any], page_num: int, img_index: int, xref: int
    ) -> Optional[Dict[str, Any]]:
        try:
            img_bytes = base_image["image"]
            img = Image.open(io.BytesIO(img_bytes))

            return {
                "page": page_num,
                "index": img_index,
                "format": base_image["ext"],
                "size": img.size,
                "mode": img.mode,
                "colorspace": base_image.get("colorspace", ""),
                "xref": xref,
                "path": f'page_{page_num}_img_{img_index}.{base_image["ext"]}',
            }
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return None

    def _get_metadata(self, doc) -> Dict[str, Any]:
        return {
            "pages": len(doc),
            "format": "PDF",
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "creation_date": doc.metadata.get("creationDate", ""),
            "producer": doc.metadata.get("producer", ""),
        }

    def _create_page_content(
        self, text: str, source: str, page_num: int, page
    ) -> Dict[str, Any]:
        return {
            "text": text,
            "source": source,
            "page": page_num,
            "dimensions": page.rect.round(),
        }

    def _create_error_page(self, page_num: int, error: str) -> Dict[str, Any]:
        return {"text": "", "error": error, "page": page_num}
