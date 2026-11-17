"""Style Mate AI - Editorial Image Renderer Component
Provides high-fidelity, crystal-clear garment image presentation.

Problem Solved:
- Catalog source images are 60x80 px thumbnails.
- Browser/Streamlit bilinear upscaling across wide columns causes extreme blur, muddiness, and pixelation.
- This component applies high-precision Lanczos upsampling (4x) with subtle unsharp enhancement.
- Encloses images in a crisp, clean white showcase frame with `object-fit: contain` and CSS `crisp-edges`
  to guarantee zero stretching, preserved aspect ratios, and sharp contrast on Retina displays.
"""

import os
import io
import base64
from pathlib import Path
from PIL import Image, ImageFilter
import streamlit as st


@st.cache_data(max_entries=1500, show_spinner=False)
def get_crisp_image_base64(image_path: str, target_width: int = 240, target_height: int = 320) -> str:
    """Load image from disk, apply high-quality Lanczos super-sampling if thumbnail, and return JPEG base64."""
    if not os.path.exists(image_path):
        return ""

    try:
        with Image.open(image_path) as im:
            im = im.convert("RGB")
            w, h = im.size

            # If image is small thumbnail (like the 60x80 catalog photos)
            if w < target_width or h < target_height:
                scale = max(target_width / w, target_height / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                im = im.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
                # Apply subtle unsharp enhancement to define crisp fabric textures and edges
                im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=100, threshold=2))
            elif w > target_width * 2 or h > target_height * 2:
                # Constrain oversize photos to avoid massive base64 network payloads
                im.thumbnail((target_width * 2, target_height * 2), Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=88)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        return ""


def render_crisp_garment_html(
    image_path: str,
    max_height: int = 220,
    max_width: int = 180,
    bg_color: str = "#FFFFFF",
    container_height: int = 230
) -> str:
    """Generate HTML snippet rendering the garment in a sharp, framed showcase."""
    b64 = get_crisp_image_base64(image_path)
    if not b64:
        return f"""
        <div style="height:{container_height}px;background:#FAF8F5;border:1px solid #E8E3DA;border-radius:10px;
                    display:flex;align-items:center;justify-content:center;color:#8C827A;font-size:12px;margin-bottom:8px;">
            Image unavailable
        </div>
        """

    return f"""
    <div style="height:{container_height}px;background:{bg_color};border:1px solid #E8E3DA;border-radius:10px;
                display:flex;align-items:center;justify-content:center;padding:12px;overflow:hidden;margin-bottom:8px;
                box-shadow:inset 0 1px 3px rgba(0,0,0,0.02);">
        <img src="data:image/jpeg;base64,{b64}" 
             style="max-height:100%;max-width:{max_width}px;object-fit:contain;
                    image-rendering:-webkit-optimize-contrast;image-rendering:crisp-edges;
                    filter:drop-shadow(0 2px 8px rgba(28,25,23,0.08));" />
    </div>
    """


def render_inspector_garment_html(
    image_path: str,
    max_height: int = 340,
    max_width: int = 280,
    bg_color: str = "#FFFFFF"
) -> str:
    """Generate HTML snippet for the detailed inspection panel."""
    b64 = get_crisp_image_base64(image_path, target_width=360, target_height=480)
    if not b64:
        return f"""
        <div style="height:{max_height}px;background:#FAF8F5;border:1px solid #E8E3DA;border-radius:12px;
                    display:flex;align-items:center;justify-content:center;color:#8C827A;font-size:13px;">
            Image unavailable
        </div>
        """

    return f"""
    <div style="height:{max_height}px;background:{bg_color};border:1px solid #E8E3DA;border-radius:12px;
                display:flex;align-items:center;justify-content:center;padding:18px;overflow:hidden;
                box-shadow:inset 0 1px 4px rgba(0,0,0,0.03);">
        <img src="data:image/jpeg;base64,{b64}" 
             style="max-height:100%;max-width:{max_width}px;object-fit:contain;
                    image-rendering:-webkit-optimize-contrast;image-rendering:crisp-edges;
                    filter:drop-shadow(0 4px 16px rgba(28,25,23,0.12));" />
    </div>
    """
