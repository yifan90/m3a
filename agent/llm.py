"""
LLM Integration - Abstract base and implementations.
"""

import base64
import io
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Any

from PIL import Image


class BaseLLM(ABC):
    """Abstract base class for LLM integration."""

    @abstractmethod
    def predict(
        self,
        prompt: str,
        images: Optional[List[Image.Image]] = None
    ) -> Tuple[str, Any]:
        """
        Call the LLM with a prompt and optional images.

        Args:
            prompt: Text prompt
            images: Optional list of PIL images

        Returns:
            Tuple of (response_text, raw_response)
        """
        pass


class OpenAICompatibleLLM(BaseLLM):
    """LLM client compatible with OpenAI API format."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "gpt-4o",
        max_tokens: int = 4096,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens

        try:
            from openai import OpenAI
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")

    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL image to base64 string."""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def predict(
        self,
        prompt: str,
        images: Optional[List[Image.Image]] = None
    ) -> Tuple[str, Any]:
        """Call the LLM."""
        content = []

        # Add images first
        if images:
            for img in images:
                b64 = self._image_to_base64(img)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"}
                })

        # Add text prompt
        content.append({"type": "text", "text": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
            max_tokens=self.max_tokens,
        )

        text = response.choices[0].message.content
        return text, response
