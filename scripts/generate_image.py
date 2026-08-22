#!/usr/bin/env python3
"""
Stage 6 — Maia Image Generation Script
NZ Travel Blog — AI Content Engine

Runs SDXL-Turbo locally via diffusers (no ComfyUI needed).
Model downloads automatically from HuggingFace on first run (~6.9 GB, cached).

Usage:
    # Generate + upload to Cloudinary:
    python generate_image.py --style flat_editorial --prompt "..." --slug "auckland-cafes"

    # Upload an existing image to Cloudinary only:
    python generate_image.py --upload output_images/my-image.png --slug "auckland-cafes"

    # Check GPU availability:
    python generate_image.py --check
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration (loaded from .env or environment)
# ---------------------------------------------------------------------------

def load_env():
    """Load .env file from project root if it exists."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())

load_env()

CLOUDINARY_CLOUD = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_KEY   = os.environ.get("CLOUDINARY_API_KEY", "")
CLOUDINARY_SEC   = os.environ.get("CLOUDINARY_API_SECRET", "")

OUTPUT_DIR = Path(__file__).parent.parent / "output_images"
OUTPUT_DIR.mkdir(exist_ok=True)

# HuggingFace model ID — downloads automatically on first run
MODEL_ID = "stabilityai/sdxl-turbo"

# ---------------------------------------------------------------------------
# Negative prompt — hardcoded anti-slop block (used for ALL generations)
# ---------------------------------------------------------------------------

NEGATIVE_PROMPT = (
    "photorealistic, photograph, photo, camera, real person, face, human body, "
    "text, watermark, signature, blurry, low quality, nsfw, recognisable landmark, "
    "building name, logo, gradient mesh, glowing orbs, neon, 3d render, cgi, "
    "smooth gradients, airbrushed"
)

# ---------------------------------------------------------------------------
# GPU check
# ---------------------------------------------------------------------------

def check_gpu() -> str:
    """Return device string: 'cuda', 'mps', or 'cpu'."""
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"[OK] GPU: {name} ({vram:.1f} GB VRAM) - CUDA")
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            print("[OK] GPU: Apple Silicon MPS")
            return "mps"
        else:
            print("[WARN] GPU not found - generation will run on CPU (~2-5 min)")
            return "cpu"
    except ImportError:
        print("[ERR] torch not installed: pip install torch")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Image generation via diffusers + SDXL-Turbo
# ---------------------------------------------------------------------------

def generate_image(style: str, prompt: str, slug: str) -> Path:
    """
    Generate a 1024x1024 image using SDXL-Turbo via diffusers.
    Model is downloaded automatically on first run (~6.9 GB, cached to ~/.cache/huggingface/).
    Returns path to saved PNG.
    """
    try:
        import torch
        from diffusers import AutoPipelineForText2Image
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("   Установи: pip install diffusers transformers accelerate torch")
        sys.exit(1)

    device = check_gpu()

    print(f"\n[Maia] Generating image...")
    print(f"   Style  : {style}")
    print(f"   Slug   : {slug}")
    print(f"   Prompt : {prompt[:100]}...")
    print(f"\n[...] Loading SDXL-Turbo (first run downloads ~6.9 GB, then cached)...")

    # Load pipeline
    dtype = torch.float16 if device == "cuda" else torch.float32
    pipe = AutoPipelineForText2Image.from_pretrained(
        MODEL_ID,
        torch_dtype=dtype,
        variant="fp16" if device == "cuda" else None,
    )
    pipe = pipe.to(device)

    # Memory optimization for 8-10 GB VRAM cards
    if device == "cuda":
        pipe.enable_attention_slicing()

    print("[...] Generating (SDXL-Turbo: 4 steps, ~5-15 sec on GPU)...")

    # SDXL-Turbo optimal settings: CFG=0.0, 4 steps, no negative prompt needed
    # (Turbo is distilled — negative prompt has minimal effect, but we keep it for safety)
    result = pipe(
        prompt=prompt,
        num_inference_steps=4,
        guidance_scale=0.0,   # SDXL-Turbo is distilled — CFG must be 0.0
        height=1024,
        width=1024,
        generator=torch.Generator(device=device).manual_seed(int(time.time()) % (2**32)),
    )

    image = result.images[0]

    # Save locally
    output_path = OUTPUT_DIR / f"{slug}.png"
    image.save(output_path)
    print(f"\n[OK] Image saved: {output_path}")

    # Free VRAM
    if device == "cuda":
        import gc
        del pipe
        torch.cuda.empty_cache()
        gc.collect()

    return output_path


# ---------------------------------------------------------------------------
# Cloudinary upload (stdlib only — no SDK required)
# ---------------------------------------------------------------------------

def upload_to_cloudinary(image_path: Path, slug: str) -> str:
    """
    Upload image to Cloudinary using signed upload.
    Returns the secure_url of the uploaded image.
    """
    if not CLOUDINARY_CLOUD or not CLOUDINARY_KEY or not CLOUDINARY_SEC:
        raise ValueError(
            "Cloudinary credentials not set. "
            "Create a .env file with CLOUDINARY_CLOUD_NAME, "
            "CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET"
        )

    timestamp  = str(int(time.time()))
    public_id  = f"nz-travel/{slug}"

    # Build Cloudinary signature
    params_to_sign = f"public_id={public_id}&timestamp={timestamp}"
    signature = hashlib.sha1(
        (params_to_sign + CLOUDINARY_SEC).encode()
    ).hexdigest()

    # Read image bytes
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Build multipart form body manually (no requests lib needed)
    boundary = "----MaiaFormBoundary" + uuid.uuid4().hex
    body_parts = []

    def add_field(name: str, value: str):
        body_parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        )

    add_field("api_key",   CLOUDINARY_KEY)
    add_field("timestamp", timestamp)
    add_field("signature", signature)
    add_field("public_id", public_id)
    add_field("overwrite", "true")

    # File field
    body_parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{image_path.name}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    )

    body = (
        "".join(body_parts).encode()
        + image_data
        + f"\r\n--{boundary}--\r\n".encode()
    )

    upload_url = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD}/image/upload"
    req = urllib.request.Request(
        upload_url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        result = json.loads(r.read())

    return result["secure_url"]


def upload_image(image_path: Path, slug: str) -> str:
    print(f"\n[...] Uploading to Cloudinary...")
    url = upload_to_cloudinary(image_path, slug)
    print(f"[OK] Cloudinary URL: {url}")
    return url


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Maia — Stage 6 Image Generator (SDXL-Turbo via diffusers)"
    )
    parser.add_argument(
        "--style", choices=["flat_editorial", "risograph"],
        help="Visual style to use"
    )
    parser.add_argument("--prompt", type=str, help="Full image generation prompt")
    parser.add_argument("--slug",   type=str, help="Article slug (used for filename)")
    parser.add_argument(
        "--upload", type=str,
        help="Path to existing image to upload to Cloudinary (skips generation)"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Check GPU availability and exit"
    )

    args = parser.parse_args()

    # --- Check mode ---
    if args.check:
        check_gpu()
        sys.exit(0)

    # --- Upload-only mode ---
    if args.upload:
        if not args.slug:
            print("[ERR] Specify --slug for upload")
            sys.exit(1)
        url = upload_image(Path(args.upload), args.slug)
        print(f"\n[URL] Use this in Notion: {url}")
        sys.exit(0)

    # --- Full generation + upload ---
    if not all([args.style, args.prompt, args.slug]):
        parser.print_help()
        sys.exit(1)

    image_path = generate_image(args.style, args.prompt, args.slug)
    url        = upload_image(image_path, args.slug)

    print(f"\n[DONE]")
    print(f"   Local file     : {image_path}")
    print(f"   Cloudinary URL : {url}")
    print(f"\n   Paste this URL into Notion as Cover Image:")
    print(f"   {url}")


if __name__ == "__main__":
    main()
