#!/usr/bin/env python3
"""
Final speed + quality test: optimised prompts within CLIP 77-token budget.
"""
import sys, time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.resolve()))
from generate_image import (
    NO_TEXT_PREFIX, detect_text_in_image, NEGATIVE_PROMPT,
    MODEL_ID, IMAGE_WIDTH, IMAGE_HEIGHT, MAX_RETRIES
)

import torch
from diffusers import AutoPipelineForText2Image, AutoencoderKL

# Optimised prompts - within 77-token CLIP budget
# NO_TEXT_PREFIX is prepended by script (~12 tokens) + body <= 65 tokens
test_cases = [
    {
        "slug": "final-test-queenstown-hikes",
        "prompt": (
            "Risograph screen print. Mountain ridge, hiking trail, fern frond. "
            "New Zealand. Two-color print, grain texture, halftone dots. "
            "Teal and terracotta on cream."
        ),
    },
    {
        "slug": "final-test-auckland-coffee",
        "prompt": (
            "Flat vector illustration. Espresso cup, pour-over dripper, coffee beans. "
            "New Zealand. Geometric shapes, flat silhouettes. "
            "Sage green, terracotta, warm cream."
        ),
    },
    {
        "slug": "final-test-wellington-guide",
        "prompt": (
            "Flat vector illustration. Harbour ferry, coastal hills, street lamp. "
            "New Zealand. Geometric shapes, flat silhouettes. "
            "Sage green, terracotta, warm cream."
        ),
    },
]

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32
OUT = Path(__file__).parent.parent / "output_images"
OUT.mkdir(exist_ok=True)

print(f"[...] Loading SDXL-Turbo via enable_model_cpu_offload() on {device.upper()}...")
vae = AutoencoderKL.from_pretrained("madebyollin/sdxl-vae-fp16-fix", torch_dtype=dtype)
pipe = AutoPipelineForText2Image.from_pretrained(MODEL_ID, vae=vae, torch_dtype=dtype, variant="fp16")
pipe.enable_model_cpu_offload()
print("[OK] Pipeline ready.\n")

total_start = time.time()

for i, tc in enumerate(test_cases, 1):
    slug = tc["slug"]
    full_prompt = NO_TEXT_PREFIX + tc["prompt"]
    out_path = OUT / f"{slug}.png"

    # Count tokens (rough word-based estimate)
    token_estimate = len(full_prompt.split())
    print(f"[{i}/{len(test_cases)}] {slug}")
    print(f"   Prompt (~{token_estimate} words): {full_prompt[:100]}...")

    t0 = time.time()
    final_img = None

    for attempt in range(1, MAX_RETRIES + 1):
        seed = (int(time.time() * 1000) + i * 7919 + attempt * 104729) % (2**32)
        res = pipe(
            prompt=full_prompt,
            negative_prompt=NEGATIVE_PROMPT,
            num_inference_steps=4,
            guidance_scale=0.0,
            height=IMAGE_HEIGHT,
            width=IMAGE_WIDTH,
            generator=torch.Generator(device=device).manual_seed(seed),
        )
        cand = res.images[0]
        if detect_text_in_image(cand):
            if attempt < MAX_RETRIES:
                print(f"   [RETRY {attempt}] Text detected, new seed...")
                continue
        else:
            print(f"   [CLEAN] Text-free (attempt {attempt}).")
        final_img = cand
        break

    if final_img is None:
        final_img = res.images[0]

    final_img.save(out_path)
    dt = time.time() - t0
    print(f"   [OK] {final_img.size[0]}x{final_img.size[1]} in {dt:.1f}s -> {out_path.name}\n")

total_dt = time.time() - total_start
avg = total_dt / len(test_cases)
print(f"[DONE] 3 images in {total_dt:.1f}s | avg {avg:.1f}s/image")
print(f"Files: {OUT}")
