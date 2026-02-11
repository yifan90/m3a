"""
OmniParser Server API - FastAPI application.
"""

import base64
import io
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

from .omniparser_service import OmniParserService


# ============================================================================
# Request/Response Models
# ============================================================================

class ParseRequest(BaseModel):
    """Request to parse an image."""
    image: str  # Base64 encoded image
    box_threshold: float = 0.05
    iou_threshold: float = 0.1
    use_paddleocr: bool = True
    return_labeled_image: bool = True


class UIElementResponse(BaseModel):
    """A detected UI element."""
    index: int
    type: str
    content: str
    bbox: list  # [x, y, width, height]
    center: list  # [x, y]
    is_clickable: bool


class ParseResponse(BaseModel):
    """Response from parsing an image."""
    elements: list[UIElementResponse]
    labeled_image: Optional[str] = None  # Base64 encoded labeled image
    image_size: list  # [width, height]
    parse_time: float  # seconds


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    models_loaded: bool
    device: str


# ============================================================================
# Global Service Instance
# ============================================================================

# Will be initialized in lifespan
omniparser_service: Optional[OmniParserService] = None


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global omniparser_service

    # Startup: Load models
    if omniparser_service is None:
        omniparser_service = OmniParserService()
    omniparser_service.load_models()

    yield

    # Shutdown: Cleanup if needed
    pass


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="OmniParser Server",
    description="HTTP API for OmniParser screen parsing",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if omniparser_service and omniparser_service.is_loaded else "initializing",
        models_loaded=omniparser_service.is_loaded if omniparser_service else False,
        device=omniparser_service.device if omniparser_service else "unknown",
    )


@app.post("/parse", response_model=ParseResponse)
async def parse_image(request: ParseRequest):
    """Parse an image and return detected UI elements."""
    if not omniparser_service or not omniparser_service.is_loaded:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # Parse
        labeled_image, elements, parse_time = omniparser_service.parse(
            image,
            box_threshold=request.box_threshold,
            iou_threshold=request.iou_threshold,
            use_paddleocr=request.use_paddleocr,
        )

        # Encode labeled image if requested
        labeled_image_b64 = None
        if request.return_labeled_image:
            buffer = io.BytesIO()
            labeled_image.save(buffer, format="PNG")
            labeled_image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return ParseResponse(
            elements=[UIElementResponse(**e) for e in elements],
            labeled_image=labeled_image_b64,
            image_size=[image.width, image.height],
            parse_time=parse_time,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Server Runner
# ============================================================================

def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    omniparser_path: Optional[str] = None,
    device: str = "cuda",
):
    """Run the OmniParser server."""
    import uvicorn

    global omniparser_service
    omniparser_service = OmniParserService(
        omniparser_path=omniparser_path,
        device=device,
    )

    print(f"Starting OmniParser Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
