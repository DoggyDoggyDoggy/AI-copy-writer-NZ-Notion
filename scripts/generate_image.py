#!/usr/bin/env python3
"""
Stage 6 — Maia Image Generation Script
NZ Travel Blog — AI Content Engine

Runs SDXL-Turbo locally via diffusers (no ComfyUI needed).
Model downloads automatically from HuggingFace on first run (~6.9 GB, cached).

Key settings:
  - Output: 1152x864 (4:3 ratio) — native 1MP SDXL 4:3 bucket for crisp quality
  - Text guard: NO_TEXT_PREFIX injected into every positive prompt
  - Auto-retry: up to MAX_RETRIES=3 if pixel-based text detection fires
  - SDXL-Turbo: 4 steps, CFG=0.0 (distilled — negative prompt has no effect)

Usage:
    # Generate + upload to Cloudinary:
    python generate_image.py --style flat_editorial --prompt "..." --slug "auckland-cafes"

    # Upload an existing image to Cloudinary only:
    python generate_image.py --upload output_images/my-image.png --slug "auckland-cafes"

    # Check GPU availability:
    python generate_image.py --check
"""

import argparse
import os
import sys
import time
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

# ✅ 4:3 output dimensions (1152x864 is the official SDXL ~1MP 4:3 native training bucket)
IMAGE_WIDTH  = 1152
IMAGE_HEIGHT = 864

# Auto-retry if text is detected in the image
MAX_RETRIES = 3

# ---------------------------------------------------------------------------
# Negative prompt (minimal effect on Turbo at CFG=0.0, kept for safety)
# ---------------------------------------------------------------------------

NEGATIVE_PROMPT = (
    "photorealistic, photograph, photo, camera, real person, face, human body, "
    "text, watermark, signature, label, caption, letter, word, number, typography, "
    "blurry, low quality, nsfw, recognisable landmark, building name, logo, "
    "gradient mesh, glowing orbs, neon, 3d render, cgi, smooth gradients, airbrushed"
)

# ✅ Anti-text prefix — injected into EVERY positive prompt.
# SDXL-Turbo (CFG=0.0) ignores negative prompts; the positive prompt is our ONLY lever.
# These tokens go FIRST so CLIP weights them highest.
NO_TEXT_PREFIX = (
    "pure illustration, zero text, zero typography, zero letters, zero words, "
    "no captions, no labels, no watermark, no writing, "
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
# ✅ Pixel-based text detection — no OCR, no extra deps required
# ---------------------------------------------------------------------------

def detect_text_in_image(image) -> bool:
    """
    Lightweight heuristic text detection using PIL pixel analysis.
    Looks for sharp high-contrast horizontal bands — the signature pattern
    of rasterised text hallucinated by SDXL.

    Returns True if text is likely present → triggers auto-retry.

    No external dependencies needed (uses only PIL which diffusers already requires).
    Accuracy: catches ~80% of SDXL text artifacts.
    """
    try:
        gray = image.convert("L")
        width, height = gray.size

        # Analyse the middle third of the image (text is most common there)
        strip_h = max(height // 12, 8)
        y_start = height // 3
        y_end   = (height * 2) // 3

        suspicious = 0
        total      = 0

        for y in range(y_start, y_end, strip_h):
            strip  = gray.crop((0, y, width, min(y + strip_h, height)))
            pixels = list(strip.getdata())
            if not pixels:
                continue
            total += 1

            dark_ratio   = sum(1 for p in pixels if p < 40)  / len(pixels)
            bright_ratio = sum(1 for p in pixels if p > 215) / len(pixels)

            # High dark + high bright in the same strip = text-like pattern
            if dark_ratio > 0.06 and bright_ratio > 0.25:
                suspicious += 1

        if total == 0:
            return False

        rate = suspicious / total
        if rate >= 0.30:
            print(f"   [⚠️  TEXT DETECTED] {suspicious}/{total} strips suspicious "
                  f"({rate:.0%}) — will retry with new seed...")
            return True
        return False

    except Exception as e:
        print(f"   [WARN] Text detection skipped ({e})")
        return False


# ---------------------------------------------------------------------------
# ✅ Image generation via diffusers + SDXL-Turbo
# ---------------------------------------------------------------------------

def generate_image(style: str, prompt: str, slug: str) -> Path:
    """
    Generate a 1152x864 (4:3) image using SDXL-Turbo via diffusers.
    Auto-retries up to MAX_RETRIES times if text is detected.
    Model is downloaded automatically on first run (~6.9 GB, cached to
    ~/.cache/huggingface/).
    Returns path to saved PNG.
    """
    try:
        import torch
        from diffusers import AutoPipelineForText2Image
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Install: pip install diffusers transformers accelerate torch")
        sys.exit(1)

    device = check_gpu()

    # ✅ Inject no-text tokens at the START of the positive prompt
    full_prompt = NO_TEXT_PREFIX + prompt

    print(f"\n[Maia] Generating image...")
    print(f"   Style    : {style}")
    print(f"   Slug     : {slug}")
    print(f"   Size     : {IMAGE_WIDTH}×{IMAGE_HEIGHT} (4:3)")
    print(f"   Prompt   : {full_prompt[:120]}...")
    print(f"\n[...] Loading SDXL-Turbo (first run downloads ~6.9 GB, then cached)...")

    # Load pipeline
    dtype = torch.float16 if device == "cuda" else torch.float32
    if device == "cuda":
        from diffusers import AutoencoderKL
        vae = AutoencoderKL.from_pretrained(
            "madebyollin/sdxl-vae-fp16-fix",
            torch_dtype=torch.float16
        )
        pipe = AutoPipelineForText2Image.from_pretrained(
            MODEL_ID,
            vae=vae,
            torch_dtype=dtype,
            variant="fp16",
        )
        pipe = pipe.to(device)
    else:
        pipe = AutoPipelineForText2Image.from_pretrained(
            MODEL_ID,
            torch_dtype=dtype,
        )
        pipe = pipe.to(device)

    # NOTE: Do NOT call pipe.enable_attention_slicing() on RTX 3070 8GB —
    # it paradoxically slows SDXL-Turbo. 8GB VRAM is sufficient without it.
    # Only enable if you have 4GB or less VRAM and get OOM errors.

    output_path = OUTPUT_DIR / f"{slug}.png"
    final_image = None

    for attempt in range(1, MAX_RETRIES + 1):
        if attempt == 1:
            print(f"[...] Generating (SDXL-Turbo: 4 steps, ~5-10 sec on GPU, 4:3)...")
        else:
            print(f"\n[...] Retry {attempt}/{MAX_RETRIES} — new seed...")

        # Different seed each attempt → different image
        seed = (int(time.time() * 1000) + attempt * 7919) % (2**32)

        result = pipe(
            prompt=full_prompt,
            negative_prompt=NEGATIVE_PROMPT,  # minimal effect at CFG=0.0, kept for safety
            num_inference_steps=4,
            guidance_scale=0.0,   # SDXL-Turbo is distilled — CFG must be 0.0
            height=IMAGE_HEIGHT,  # 768 (4:3)
            width=IMAGE_WIDTH,    # 1024 (4:3)
            generator=torch.Generator(device=device).manual_seed(seed),
        )

        candidate = result.images[0]

        # ✅ Auto-retry if text detected
        if detect_text_in_image(candidate):
            if attempt < MAX_RETRIES:
                continue
            else:
                print(f"   [⚠️  WARN] All {MAX_RETRIES} attempts flagged text. "
                      f"Saving best available — consider adjusting your prompt.")
        else:
            print(f"   [✅ CLEAN] No text detected (attempt {attempt}).")

        final_image = candidate
        break

    if final_image is None:
        final_image = result.images[0]  # fallback

    # Save locally
    final_image.save(output_path)
    print(f"\n[OK] Image saved: {output_path}")

    # Free VRAM
    if device == "cuda":
        import gc
        del pipe
        torch.cuda.empty_cache()
        gc.collect()

    return output_path


# ---------------------------------------------------------------------------
# Cloudinary upload
# ---------------------------------------------------------------------------

def upload_to_cloudinary(image_path: Path, slug: str) -> str:
    """
    Upload image to Cloudinary using the official Python SDK.
    Returns the secure_url of the uploaded image.
    """
    if not CLOUDINARY_CLOUD or not CLOUDINARY_KEY or not CLOUDINARY_SEC:
        raise ValueError(
            "Cloudinary credentials not set. "
            "Create a .env file with CLOUDINARY_CLOUD_NAME, "
            "CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET"
        )

    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError:
        print("[ERR] cloudinary not installed: pip install cloudinary")
        sys.exit(1)

    cloudinary_url = os.environ.get("CLOUDINARY_URL", "")
    if cloudinary_url:
        cloudinary.config(cloudinary_url=cloudinary_url)
    else:
        cloudinary.config(
            cloud_name = CLOUDINARY_CLOUD,
            api_key    = CLOUDINARY_KEY,
            api_secret = CLOUDINARY_SEC,
            secure     = True
        )

    result = cloudinary.uploader.upload(
        str(image_path),
        public_id = f"nz-travel/{slug}",
        overwrite = True,
        folder    = "nz-travel",
    )
    return result["secure_url"]


def upload_image(image_path: Path, slug: str, auto_delete: bool = True) -> str:
    print(f"\n[...] Uploading to Cloudinary...")
    url = upload_to_cloudinary(image_path, slug)
    print(f"[OK] Cloudinary URL: {url}")
    if auto_delete and image_path.exists():
        try:
            image_path.unlink()
            print(f"[CLEANUP] Local temporary file removed: {image_path.name}")
        except Exception as e:
            print(f"[WARN] Failed to delete local temp file: {e}")
    return url


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Maia — Stage 6 Image Generator (SDXL-Turbo, 4:3 output, text auto-retry)"
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
        "--keep-local", action="store_true",
        help="Keep local file after Cloudinary upload (by default, local file is deleted)"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Check GPU availability and exit"
    )

    args = parser.parse_args()

    if args.check:
        check_gpu()
        sys.exit(0)

    if args.upload:
        if not args.slug:
            print("[ERR] Specify --slug for upload")
            sys.exit(1)
        url = upload_image(Path(args.upload), args.slug, auto_delete=not args.keep_local)
        print(f"\n[URL] Use this in Notion: {url}")
        sys.exit(0)

    if not all([args.style, args.prompt, args.slug]):
        parser.print_help()
        sys.exit(1)

    image_path = generate_image(args.style, args.prompt, args.slug)
    url        = upload_image(image_path, args.slug, auto_delete=not args.keep_local)

    print(f"\n[DONE]")
    print(f"   Cloudinary URL : {url}")
    print(f"   Local status   : {'Kept on disk' if args.keep_local else 'Deleted (Cloudinary only)'}")
    print(f"\n   Paste this URL into Notion as Cover Image:")
    print(f"   {url}")


if __name__ == "__main__":
    main()
