#!/usr/bin/env python3
"""
Maia Batch Cover Generator & Cloudinary Uploader
NZ Travel Blog — AI Content Engine

Generates 1152x864 (4:3) cover illustrations locally via SDXL-Turbo for all articles,
uploads them to Cloudinary, and saves the resulting URLs.

Key settings:
  - Output: 1152x864 (4:3 ratio) — native 1MP SDXL 4:3 bucket for crisp quality
  - Text guard: NO_TEXT_PREFIX injected at start of every positive prompt
  - Auto-retry: up to MAX_RETRIES=3 if pixel-based text detection fires
  - SDXL-Turbo: 4 steps, CFG=0.0 (distilled — negative prompt has no effect)
"""

import json
import os
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Configuration & Environment
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / "output_images"
OUTPUT_DIR.mkdir(exist_ok=True)

SCRATCH_DIR = Path(r"C:\Users\pedan\.gemini\antigravity-ide\brain\c262a2d1-69a8-4d71-87ae-509641f1839a\scratch")
PROMPTS_FILE = SCRATCH_DIR / "maia_prompts_map.json"
RESULTS_FILE = SCRATCH_DIR / "batch_results.json"

def load_env():
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())

load_env()

# Configure Cloudinary
try:
    import cloudinary
    import cloudinary.uploader
    cloudinary_url = os.environ.get("CLOUDINARY_URL", "")
    if cloudinary_url:
        cloudinary.config(cloudinary_url=cloudinary_url)
    else:
        cloudinary.config(
            cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", "hmiwtp0w"),
            api_key=os.environ.get("CLOUDINARY_API_KEY", "591616998429991"),
            api_secret=os.environ.get("CLOUDINARY_API_SECRET", "lE18ju6D8jOa6QpdCKiM4iwYSWY"),
            secure=True
        )
except ImportError:
    print("[ERR] cloudinary not installed: pip install cloudinary")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Image generation settings
# ---------------------------------------------------------------------------

# ✅ 4:3 output dimensions (1152x864 is the official SDXL ~1MP 4:3 native training bucket)
IMAGE_WIDTH  = 1152
IMAGE_HEIGHT = 864

# Auto-retry if text detected
MAX_RETRIES = 3

# ✅ Anti-text prefix — injected into EVERY positive prompt.
# SDXL-Turbo (CFG=0.0) ignores negative prompts; the positive prompt is our ONLY lever.
NO_TEXT_PREFIX = (
    "pure illustration, zero text, zero typography, zero letters, zero words, "
    "no captions, no labels, no watermark, no writing, "
)

# ---------------------------------------------------------------------------
# Pixel-based text detection (no extra deps — uses PIL only)
# ---------------------------------------------------------------------------

def detect_text_in_image(image) -> bool:
    """
    Lightweight heuristic: looks for sharp high-contrast horizontal bands
    (signature pattern of SDXL text hallucinations).
    Returns True → triggers auto-retry.
    """
    try:
        gray = image.convert("L")
        width, height = gray.size
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
            if dark_ratio > 0.06 and bright_ratio > 0.25:
                suspicious += 1
        if total == 0:
            return False
        rate = suspicious / total
        if rate >= 0.30:
            print(f"   [⚠️  TEXT DETECTED] {suspicious}/{total} strips suspicious "
                  f"({rate:.0%}) — retrying...")
            return True
        return False
    except Exception as e:
        print(f"   [WARN] Text detection skipped ({e})")
        return False


# ---------------------------------------------------------------------------
# Batch Processing Engine
# ---------------------------------------------------------------------------

def main():
    if not PROMPTS_FILE.exists():
        print(f"[ERR] Prompts map file not found: {PROMPTS_FILE}")
        sys.exit(1)

    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)

    print(f"==================================================")
    print(f"🎨 Maia Batch Image Generation Pipeline")
    print(f"Total articles to process: {len(articles)}")
    print(f"==================================================")

    # Load existing results if resuming
    results = {}
    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
                for item in existing:
                    results[item["id"]] = item
            print(f"Found {len(results)} already processed items in results.")
        except Exception:
            pass

    # Check GPU and load SDXL-Turbo with ultra-fast FP16-fixed VAE
    import torch
    from diffusers import AutoPipelineForText2Image, AutoencoderKL

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    print(f"[...] Loading ultra-fast SDXL-Turbo (4:3 output, ~6s per image) on {device.upper()}...", flush=True)

    if device == "cuda":
        vae = AutoencoderKL.from_pretrained(
            "madebyollin/sdxl-vae-fp16-fix",
            torch_dtype=torch.float16
        )
        pipe = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/sdxl-turbo",
            vae=vae,
            torch_dtype=dtype,
            variant="fp16",
        )
        pipe.enable_model_cpu_offload()
    else:
        pipe = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/sdxl-turbo",
            torch_dtype=dtype,
        )
        pipe = pipe.to(device)

    print("[OK] Ultra-Fast Pipeline loaded and ready in VRAM.\n", flush=True)

    start_total_time = time.time()
    count_generated = 0
    count_uploaded = 0

    for idx, article in enumerate(articles, start=1):
        page_id = article["id"]
        slug = article["slug"]
        title = article["title"]
        city = article["city"]
        style = article["style"]
        prompt = article["prompt"]

        print(f"\n[{idx}/{len(articles)}] 📄 [{city.upper()}] {title}", flush=True)
        print(f"   Slug: {slug} | Style: {style}", flush=True)

        image_path = OUTPUT_DIR / f"{slug}.png"

        # Check if already generated
        if not image_path.exists():
            print(f"   [🎨 Maia] Generating {IMAGE_WIDTH}x{IMAGE_HEIGHT} (4:3) illustration...", flush=True)
            gen_start = time.time()

            # ✅ Inject no-text prefix at start of prompt
            full_prompt = NO_TEXT_PREFIX + prompt

            final_image = None
            for attempt in range(1, MAX_RETRIES + 1):
                if attempt > 1:
                    print(f"   [↩️  RETRY {attempt}/{MAX_RETRIES}] New seed...", flush=True)

                seed = (int(time.time() * 1000) + idx * 1000 + attempt * 7919) % (2**32)
                result = pipe(
                    prompt=full_prompt,
                    num_inference_steps=4,
                    guidance_scale=0.0,
                    height=IMAGE_HEIGHT,   # 768 (4:3)
                    width=IMAGE_WIDTH,     # 1024 (4:3)
                    generator=torch.Generator(device=device).manual_seed(seed),
                )
                candidate = result.images[0]

                if detect_text_in_image(candidate):
                    if attempt < MAX_RETRIES:
                        continue
                    else:
                        print(f"   [⚠️  WARN] All {MAX_RETRIES} attempts had text. Saving best available.", flush=True)
                else:
                    print(f"   [✅ CLEAN] No text detected (attempt {attempt}).", flush=True)

                final_image = candidate
                break

            if final_image is None:
                final_image = result.images[0]

            final_image.save(image_path)
            gen_duration = time.time() - gen_start
            print(f"   [OK] Generated in {gen_duration:.1f}s -> {image_path.name}", flush=True)
            count_generated += 1
        else:
            print(f"   [INFO] Local image already exists: {image_path.name}", flush=True)

        # Check if already uploaded
        cloudinary_url = None
        if page_id in results and results[page_id].get("cloudinary_url"):
            cloudinary_url = results[page_id]["cloudinary_url"]
            print(f"   [INFO] Already uploaded: {cloudinary_url}", flush=True)
        else:
            upload_res = cloudinary.uploader.upload(
                str(image_path),
                public_id=f"nz-travel/{slug}",
                overwrite=True,
                folder="nz-travel",
            )
            cloudinary_url = upload_res["secure_url"]
            print(f"   [OK] Cloudinary URL: {cloudinary_url}", flush=True)
            count_uploaded += 1

            # Auto-cleanup: remove local temp file immediately after Cloudinary upload
            if image_path.exists():
                try:
                    image_path.unlink()
                    print(f"   [CLEANUP] Deleted local temporary file: {image_path.name}", flush=True)
                except Exception as e:
                    print(f"   [WARN] Could not delete local temp file: {e}", flush=True)

        results[page_id] = {
            "id": page_id,
            "city": city,
            "title": title,
            "slug": slug,
            "style": style,
            "prompt": prompt,
            "cloudinary_url": cloudinary_url,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Save progress incrementally to scratch/batch_results.json
        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(results.values()), f, ensure_ascii=False, indent=2)

    total_duration = time.time() - start_total_time
    print(f"\n==================================================", flush=True)
    print(f"🎉 Batch generation & upload complete in {total_duration/60:.1f} minutes!", flush=True)
    print(f"   Generated : {count_generated}", flush=True)
    print(f"   Uploaded  : {count_uploaded}", flush=True)
    print(f"   Total in results: {len(results)}", flush=True)
    print(f"   Saved to  : {RESULTS_FILE}", flush=True)
    print(f"==================================================", flush=True)

if __name__ == "__main__":
    main()
