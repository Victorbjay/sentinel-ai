import base64
import hashlib
import io
import logging
from typing import Dict, Any, Optional
import httpx
from PIL import Image, ExifTags
from app.core.config import settings

logger = logging.getLogger(__name__)


def inspect_image_metadata(image_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Safely inspects image metadata (dimensions, format, EXIF tags, editing software)
    without making any automated fake/real verdict (Track 1D).
    """
    sha256 = hashlib.sha256(image_bytes).hexdigest()[:16]
    info: Dict[str, Any] = {
        "filename": filename,
        "size_bytes": len(image_bytes),
        "sha256_prefix": sha256,
        "format": "unknown",
        "dimensions": None,
        "has_exif": False,
        "software_tag": None,
        "exif_summary": [],
    }

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            info["format"] = img.format or "unknown"
            info["dimensions"] = f"{img.width}x{img.height}"
            exif_data = img.getexif()
            if exif_data and len(exif_data) > 0:
                info["has_exif"] = True
                for tag_id, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                    if tag_name in ("Software", "Make", "Model", "DateTime", "DateTimeOriginal"):
                        val_str = str(value)[:80]
                        info["exif_summary"].append(f"{tag_name}: {val_str}")
                        if tag_name == "Software":
                            info["software_tag"] = val_str
    except Exception as e:
        info["metadata_note"] = f"Could not parse image headers: {e}"

    return info


async def _try_gemini_vision_screen(image_bytes: bytes, mime_type: str) -> Optional[str]:
    """Optional Gemini 2.0 Flash Vision extraction of visible electoral claims."""
    if not settings.GEMINI_API_KEY:
        return None

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    prompt = (
        "You are an impartial electoral verification assistant (Track 1D). "
        "Do NOT declare the image real or fake and do NOT declare election outcomes. "
        "In 3 concise bullet points: (1) transcribe any visible electoral claim or figures, "
        "(2) note any visible formatting/provenance cues a human should verify, and "
        "(3) suggest what official INEC record (e.g., Form EC8A on IReV) to compare against."
    )
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": b64}},
                ]
            }
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and parts[0].get("text"):
                        return parts[0]["text"].strip()
    except Exception as e:
        logger.warning(f"Gemini Vision screening failed: {e}")
    return None


async def screen_media_artifact(
    image_bytes: bytes,
    filename: str,
    mime_type: str = "image/jpeg",
) -> Dict[str, Any]:
    """
    Track 1D Synthetic Media Screening Assistant:
    Guides observers through verification steps rather than issuing a fake/real verdict.
    """
    metadata = inspect_image_metadata(image_bytes, filename)
    vision_notes = await _try_gemini_vision_screen(image_bytes, mime_type)

    cues = []
    if not metadata["has_exif"]:
        cues.append("No EXIF camera metadata found (common on WhatsApp/social re-uploads; not proof of manipulation).")
    if metadata["software_tag"]:
        cues.append(f"Editing software tag detected in header: '{metadata['software_tag']}'. Inspect closely.")

    checklist = [
        "1. Reverse Image Search: Check if this photo/flyer appeared in an earlier election cycle or different state.",
        "2. Official INEC Cross-Check: If this shows a polling unit result (Form EC8A), compare the PU code and signatures on official INEC IReV.",
        "3. Source Provenance: Confirm whether the image came from an official INEC channel or an anonymous forward.",
        "4. Human Verdict Only: Sentinel-AI never auto-labels media as fake or real without accredited human review.",
    ]

    return {
        "metadata": metadata,
        "automated_cues": cues,
        "vision_summary": vision_notes or (
            "Offline metadata scan completed. Add GEMINI_API_KEY in .env to enable automated OCR & visual cue extraction."
        ),
        "verification_checklist": checklist,
        "guardrail_notice": "Advisory screening only — requires human fact-checker verification.",
    }
