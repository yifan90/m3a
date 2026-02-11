"""
OmniParser Client - Remote API client for OmniParser server.
"""

import base64
import io
from typing import List, Tuple, Dict, Any

import requests
from PIL import Image

from .models import UIElement


class OmniParserClient:
    """OmniParser client that connects to a remote server."""

    def __init__(
        self,
        server_url: str = "http://localhost:8000",
        use_paddleocr: bool = True,
        timeout: int = 60,
    ):
        """
        Initialize OmniParser client.

        Args:
            server_url: URL of the OmniParser server
            use_paddleocr: Whether to use PaddleOCR (vs EasyOCR)
            timeout: Request timeout in seconds
        """
        self.server_url = server_url.rstrip("/")
        self.use_paddleocr = use_paddleocr
        self.timeout = timeout

    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL image to base64 string."""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def health_check(self) -> Dict[str, Any]:
        """Check if the server is healthy."""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def is_available(self) -> bool:
        """Check if server is available."""
        health = self.health_check()
        return health.get("status") == "healthy"

    def parse(
        self,
        image: Image.Image,
        box_threshold: float = 0.05,
        iou_threshold: float = 0.1,
    ) -> Tuple[Image.Image, List[UIElement]]:
        """
        Parse image via remote server.

        Args:
            image: PIL Image to parse
            box_threshold: Confidence threshold for detection
            iou_threshold: IoU threshold for NMS

        Returns:
            Tuple of (labeled_image, list of UIElements)
        """
        # Encode image
        image_b64 = self._image_to_base64(image)

        # Make request
        response = requests.post(
            f"{self.server_url}/parse",
            json={
                "image": image_b64,
                "box_threshold": box_threshold,
                "iou_threshold": iou_threshold,
                "use_paddleocr": self.use_paddleocr,
                "return_labeled_image": True,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()

        # Decode labeled image
        labeled_image = Image.open(io.BytesIO(base64.b64decode(data["labeled_image"])))

        # Convert to UIElement list
        ui_elements = []
        for elem in data["elements"]:
            ui_elem = UIElement(
                index=elem["index"],
                type=elem["type"],
                content=elem["content"],
                bbox=tuple(elem["bbox"]),
                center=tuple(elem["center"]),
                is_clickable=elem["is_clickable"],
            )
            ui_elements.append(ui_elem)

        return labeled_image, ui_elements
