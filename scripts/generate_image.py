#!/usr/bin/env python3
"""
Stage 6 — Maia Image Generation Script
NZ Travel Blog — AI Content Engine

Usage:
    python generate_image.py --style flat_editorial --prompt "..." --slug "auckland-cafes"
    python generate_image.py --upload output_images/auckland-cafes.png --slug "auckland-cafes"
    python generate_image.py --check  # Check if ComfyUI is running
"""

import argparse
import json
import os
import sys
import time
import uuid
import urllib.request
import urllib.error
import urllib.parse
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

COMFYUI_HOST     = os.environ.get("COMFYUI_HOST", "http://localhost:8188")
CLOUDINARY_CLOUD = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_KEY   = os.environ.get("CLOUDINARY_API_KEY", "")
CLOUDINARY_SEC   = os.environ.get("CLOUDINARY_API_SECRET", "")

OUTPUT_DIR = Path(__file__).parent.parent / "output_images"
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# ComfyUI Workflow Templates
# ---------------------------------------------------------------------------

SDXL_TURBO_WORKFLOW = {
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "cfg": 1.0,
            "denoise": 1.0,
            "latent_image": ["5", 0],
            "model": ["4", 0],
            "negative": ["7", 0],
            "positive": ["6", 0],
            "sampler_name": "euler_ancestral",
            "scheduler": "normal",
            "seed": 0,          # Will be randomised per generation
            "steps": 4           # SDXL-Turbo: 4 steps is optimal
        }
    },
    "4": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {
            "ckpt_name": "sd_xl_turbo_1.0_fp16.safetensors"
        }
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {
            "batch_size": 1,
            "height": 1024,
            "width": 1024
        }
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["4", 1],
            "text": ""           # Filled at runtime
        }
    },
    "7": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["4", 1],
            "text": "photorealistic, photograph, photo, text, watermark, signature, blurry, nsfw, face, person, human, landmark, building name, logo"
        }
    },
    "8": {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["3", 0],
            "vae": ["4", 2]
        }
    },
    "9": {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": "maia_output",
            "images": ["8", 0]
        }
    }
}

# ---------------------------------------------------------------------------
# ComfyUI API helpers
# ---------------------------------------------------------------------------

def check_comfyui() -> bool:
    """Return True if ComfyUI is reachable."""
    try:
        req = urllib.request.Request(f"{COMFYUI_HOST}/system_stats")
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def queue_prompt(workflow: dict) -> str:
    """Submit workflow to ComfyUI queue. Returns prompt_id."""
    payload = json.dumps({"prompt": workflow, "client_id": str(uuid.uuid4())}).encode()
    req = urllib.request.Request(
        f"{COMFYUI_HOST}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    return data["prompt_id"]


def wait_for_image(prompt_id: str, timeout: int = 120) -> list:
    """Poll ComfyUI history until prompt is done. Returns list of output filenames."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        req = urllib.request.Request(f"{COMFYUI_HOST}/history/{prompt_id}")
        with urllib.request.urlopen(req, timeout=10) as r:
            history = json.loads(r.read())
        if prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})
            filenames = []
            for node_output in outputs.values():
                for img in node_output.get("images", []):
                    filenames.append(img["filename"])
            return filenames
        time.sleep(2)
    raise TimeoutError(f"ComfyUI did not finish within {timeout}s")


def download_image(filename: str, dest_path: Path) -> Path:
    """Download generated image from ComfyUI /view endpoint."""
    url = f"{COMFYUI_HOST}/view?filename={urllib.parse.quote(filename)}"
    urllib.request.urlretrieve(url, dest_path)
    return dest_path

# ---------------------------------------------------------------------------
# Cloudinary upload (using REST API — no SDK required)
# ---------------------------------------------------------------------------

def upload_to_cloudinary(image_path: Path, slug: str) -> str:
    """
    Upload image to Cloudinary using unsigned upload or signed upload.
    Returns the secure_url of the uploaded image.
    """
    import base64
    import hashlib

    if not CLOUDINARY_CLOUD or not CLOUDINARY_KEY or not CLOUDINARY_SEC:
        raise ValueError(
            "Cloudinary credentials not set. "
            "Add CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET to .env"
        )

    timestamp = str(int(time.time()))
    public_id = f"nz-travel/{slug}"

    # Build signature
    params_to_sign = f"public_id={public_id}&timestamp={timestamp}"
    signature = hashlib.sha1(
        (params_to_sign + CLOUDINARY_SEC).encode()
    ).hexdigest()

    # Read image
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Multipart form data (manual build — no requests lib required)
    boundary = "----FormBoundary" + uuid.uuid4().hex
    body_parts = []

    def add_field(name, value):
        body_parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        )

    add_field("api_key", CLOUDINARY_KEY)
    add_field("timestamp", timestamp)
    add_field("signature", signature)
    add_field("public_id", public_id)
    add_field("overwrite", "true")

    body_parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{image_path.name}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    )

    body = "".join(body_parts).encode() + image_data + f"\r\n--{boundary}--\r\n".encode()

    upload_url = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD}/image/upload"
    req = urllib.request.Request(
        upload_url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        result = json.loads(r.read())

    return result["secure_url"]

# ---------------------------------------------------------------------------
# Main generation pipeline
# ---------------------------------------------------------------------------

def generate_image(style: str, prompt: str, slug: str) -> Path:
    """Generate an image via ComfyUI and save locally. Returns local path."""
    print(f"\n🎨 Maia — Generating image...")
    print(f"   Style : {style}")
    print(f"   Slug  : {slug}")
    print(f"   Prompt: {prompt[:80]}...")

    # 1. Check ComfyUI
    if not check_comfyui():
        print("\n❌ ComfyUI не запущен!")
        print("   Запусти его: python main.py --listen  (в папке ComfyUI)")
        sys.exit(1)

    # 2. Build workflow
    workflow = json.loads(json.dumps(SDXL_TURBO_WORKFLOW))  # deep copy
    workflow["6"]["inputs"]["text"] = prompt
    workflow["3"]["inputs"]["seed"] = int(time.time()) % (2**32)
    workflow["9"]["inputs"]["filename_prefix"] = f"maia_{slug}"

    # 3. Queue prompt
    print("\n⏳ Отправляю в ComfyUI...")
    prompt_id = queue_prompt(workflow)
    print(f"   Queue ID: {prompt_id}")

    # 4. Wait for completion
    print("⏳ Генерация... (SDXL-Turbo: ~5-15 сек)")
    filenames = wait_for_image(prompt_id, timeout=120)

    if not filenames:
        raise RuntimeError("ComfyUI вернул пустой список файлов")

    # 5. Download image
    output_path = OUTPUT_DIR / f"{slug}.png"
    download_image(filenames[0], output_path)
    print(f"\n✅ Изображение сохранено: {output_path}")
    return output_path


def upload_image(image_path: Path, slug: str) -> str:
    """Upload image to Cloudinary and return URL."""
    print(f"\n☁️  Загружаю в Cloudinary...")
    url = upload_to_cloudinary(image_path, slug)
    print(f"✅ Cloudinary URL: {url}")
    return url


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Maia — Stage 6 Image Generator for NZ Travel Blog"
    )
    parser.add_argument("--style", choices=["flat_editorial", "risograph"],
                        help="Visual style to use")
    parser.add_argument("--prompt", type=str, help="Full image generation prompt")
    parser.add_argument("--slug", type=str, help="Article slug (used for filename)")
    parser.add_argument("--upload", type=str,
                        help="Path to existing image to upload to Cloudinary (skip generation)")
    parser.add_argument("--check", action="store_true",
                        help="Check if ComfyUI is running and exit")

    args = parser.parse_args()

    # --- Check mode ---
    if args.check:
        if check_comfyui():
            print("✅ ComfyUI запущен и отвечает")
        else:
            print("❌ ComfyUI не запущен. Запусти: python main.py --listen")
        sys.exit(0)

    # --- Upload-only mode ---
    if args.upload:
        if not args.slug:
            print("❌ Укажи --slug для загрузки")
            sys.exit(1)
        url = upload_image(Path(args.upload), args.slug)
        print(f"\n🔗 Используй этот URL в Notion: {url}")
        sys.exit(0)

    # --- Full generation + upload ---
    if not args.style or not args.prompt or not args.slug:
        parser.print_help()
        sys.exit(1)

    image_path = generate_image(args.style, args.prompt, args.slug)
    url = upload_image(image_path, args.slug)
    print(f"\n📋 Финальный Cloudinary URL:")
    print(f"   {url}")


if __name__ == "__main__":
    main()
