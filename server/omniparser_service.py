"""
OmniParser Service - Core parsing logic.
"""

import os
import base64
import io
import time
from typing import Optional, Tuple, List, Dict, Any

from PIL import Image


def _get_default_omniparser_path() -> str:
    """Get default OmniParser path relative to this file."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "OmniParser")


class OmniParserService:
    """OmniParser service for the server."""

    def __init__(
        self,
        omniparser_path: Optional[str] = None,
        weights_path: Optional[str] = None,
        device: str = "cuda",
    ):
        import sys

        if omniparser_path is None:
            omniparser_path = _get_default_omniparser_path()

        if omniparser_path not in sys.path:
            sys.path.insert(0, omniparser_path)

        self.omniparser_path = omniparser_path
        self.weights_path = weights_path or f"{omniparser_path}/weights"
        self.device = device

        self._yolo_model = None
        self._caption_model = None
        self._loaded = False

    def load_models(self):
        """Load models (call this at startup)."""
        if self._loaded:
            return

        from util.utils import get_yolo_model, get_caption_model_processor

        print("Loading OmniParser models...")
        print(f"  Device: {self.device}")
        print(f"  Weights: {self.weights_path}")

        self._yolo_model = get_yolo_model(f"{self.weights_path}/icon_detect/model.pt")
        self._caption_model = get_caption_model_processor(
            "florence2",
            f"{self.weights_path}/icon_caption_florence",
            device=self.device
        )
        self._loaded = True
        print("Models loaded!")

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def parse(
        self,
        image: Image.Image,
        box_threshold: float = 0.05,
        iou_threshold: float = 0.1,
        use_paddleocr: bool = True,
    ) -> Tuple[Image.Image, List[Dict[str, Any]], float]:
        """
        Parse an image and detect UI elements.

        Returns:
            Tuple of (labeled_image, elements_list, parse_time)
        """
        if not self._loaded:
            self.load_models()

        from util.utils import check_ocr_box, get_som_labeled_img

        start_time = time.time()
        w, h = image.size

        # Configure drawing
        box_overlay_ratio = max(image.size) / 3200
        draw_bbox_config = {
            'text_scale': 0.8 * box_overlay_ratio,
            'text_thickness': max(int(2 * box_overlay_ratio), 1),
            'text_padding': max(int(3 * box_overlay_ratio), 1),
            'thickness': max(int(3 * box_overlay_ratio), 1),
        }

        # OCR
        ocr_result, _ = check_ocr_box(
            image,
            display_img=False,
            output_bb_format='xyxy',
            easyocr_args={'paragraph': False, 'text_threshold': 0.9},
            use_paddleocr=use_paddleocr,
        )
        ocr_texts, ocr_bboxes = ocr_result

        # Parse with OmniParser
        labeled_img_b64, label_coords, parsed_elements = get_som_labeled_img(
            image,
            self._yolo_model,
            BOX_TRESHOLD=box_threshold,
            output_coord_in_ratio=True,
            ocr_bbox=ocr_bboxes,
            draw_bbox_config=draw_bbox_config,
            caption_model_processor=self._caption_model,
            ocr_text=ocr_texts,
            iou_threshold=iou_threshold,
        )

        # Decode labeled image
        labeled_image = Image.open(io.BytesIO(base64.b64decode(labeled_img_b64)))

        # Convert to element list
        elements = []
        for i, elem in enumerate(parsed_elements):
            bbox_ratio = elem['bbox']
            x1, y1, x2, y2 = bbox_ratio

            # Convert ratio to pixels
            px1, py1 = int(x1 * w), int(y1 * h)
            px2, py2 = int(x2 * w), int(y2 * h)

            elements.append({
                "index": i,
                "type": elem.get('type', 'icon'),
                "content": elem.get('content', '') or '',
                "bbox": [px1, py1, px2 - px1, py2 - py1],
                "center": [(px1 + px2) // 2, (py1 + py2) // 2],
                "is_clickable": elem.get('interactivity', True),
            })

        parse_time = time.time() - start_time
        return labeled_image, elements, parse_time
