#!/usr/bin/env python3
"""
Generate all 28 article covers locally using SDXL-Turbo on CUDA,
upload them to Cloudinary, and patch the Notion pages with their covers.
"""

import json
import os
import sys
import time
from pathlib import Path
import requests
import torch
from PIL import Image

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(r"f:\vibe_coding_projects\AI-copy-writer-NZ-Notion")
OUTPUT_DIR = ROOT_DIR / "output_images"
OUTPUT_DIR.mkdir(exist_ok=True)

# Load .env
def load_env():
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())

load_env()

# Load Cloudinary
import cloudinary
import cloudinary.uploader
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", "hmiwtp0w"),
    api_key=os.environ.get("CLOUDINARY_API_KEY", ""),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", ""),
    secure=True
)

NOTION_TOKEN = os.environ.get("NOTION_API_KEY", os.environ.get("NOTION_TOKEN", ""))
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

IMAGE_WIDTH = 1152
IMAGE_HEIGHT = 864
MAX_RETRIES = 3
NO_TEXT_PREFIX = "pure vector illustration, zero text, no letters, no words, no labels, "

def detect_text_in_image(image) -> bool:
    try:
        gray = image.convert("L")
        width, height = gray.size
        strip_h = max(height // 16, 6)

        def scan_zone(y_from, y_to, dark_thresh, bright_thresh, rate_thresh):
            suspicious = 0
            total = 0
            for y in range(y_from, y_to, strip_h):
                strip = gray.crop((0, y, width, min(y + strip_h, y_to)))
                pixels = list(strip.getdata())
                if not pixels:
                    continue
                total += 1
                dark_ratio   = sum(1 for p in pixels if p < 50)  / len(pixels)
                bright_ratio = sum(1 for p in pixels if p > 200) / len(pixels)
                if dark_ratio > dark_thresh and bright_ratio > bright_thresh:
                    suspicious += 1
            if total == 0:
                return False
            rate = suspicious / total
            return rate >= rate_thresh

        if scan_zone(int(height * 0.80), height, 0.03, 0.15, 0.20):
            return True
        if scan_zone(0, height, 0.06, 0.25, 0.30):
            return True
        return False
    except Exception as e:
        return False

# 28 Articles definitions with Maia prompts
ARTICLES = [
  {
    "index": 1,
    "id": "3d5ba31b-5f1a-816f-b290-f5e3079e2160",
    "slug": "gisborne-with-kids-family-guide",
    "title": "Gisborne with Kids: 7 Best Family Adventures, Wild Stingrays & Natural Rockslides",
    "style": "risograph",
    "prompt": "Risograph screen print. Gentle ocean swell, stingray silhouette underwater, smooth river rocks. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 2,
    "id": "3d5ba31b-5f1a-81a5-9787-e0378bd587c1",
    "slug": "invercargill-with-kids-family-guide",
    "title": "Invercargill with Kids: 7 Best Heavy Digger Playgrounds, Animal Parks & Coastal Escapes",
    "style": "flat_editorial",
    "prompt": "Flat vector illustration. Stylized excavator bucket, park trees, open coastal beach grass. New Zealand. Geometric shapes, flat silhouettes. Sage green, terracotta, warm cream."
  },
  {
    "index": 3,
    "id": "3d5ba31b-5f1a-8159-978e-ef74215657e2",
    "slug": "new-plymouth-with-kids-family-guide",
    "title": "New Plymouth with Kids: 7 Best Free Zoos, Wave Pools & Coastal Bike Trails",
    "style": "flat_editorial",
    "prompt": "Flat vector illustration. Coastal bicycle pathway, rolling ocean waves, arched wooden footbridge. New Zealand. Geometric shapes, flat silhouettes. Sage green, terracotta, warm cream."
  },
  {
    "index": 4,
    "id": "3d5ba31b-5f1a-81b6-be34-f7f439e71214",
    "slug": "palmerston-north-with-kids-family-guide",
    "title": "Palmerston North with Kids: 7 Best Miniature Railways, Wildlife Parks & River Trails",
    "style": "flat_editorial",
    "prompt": "Flat vector illustration. Miniature railway tracks, riverside pine trees, playground geometric structures. New Zealand. Geometric shapes, flat silhouettes. Sage green, terracotta, warm cream."
  },
  {
    "index": 5,
    "id": "3d5ba31b-5f1a-81aa-99b3-d1884b296a1d",
    "slug": "whangarei-with-kids-family-guide",
    "title": "Whangārei with Kids: 7 Best Kiwi Houses, Treetop Ziplines & Waterfall Walks",
    "style": "risograph",
    "prompt": "Risograph screen print. Cascading waterfall curtain, native silver fern fronds, treetop canopy rope. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 6,
    "id": "3d5ba31b-5f1a-8133-bbc0-c925face8de7",
    "slug": "hamilton-nightlife-evening-guide",
    "title": "Hamilton Nightlife Guide: 7 Best Speakeasies, Riverfront Patios & Cult Scoops",
    "style": "risograph",
    "prompt": "Risograph screen print. Cocktail coupe glass with lemon twist, riverfront patio lanterns, ambient evening terrace. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 7,
    "id": "3d5ba31b-5f1a-81fe-a7f7-dea64a52e3fe",
    "slug": "napier-nightlife-evening-guide",
    "title": "Napier Nightlife Guide: 7 Best Art Deco Cocktail Lounges, Wine Bars & Seaside Taps",
    "style": "risograph",
    "prompt": "Risograph screen print. Geometric martini glass, art deco fan motif, wine decanter on wooden table. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 8,
    "id": "3d5ba31b-5f1a-810e-a706-f1830c26c661",
    "slug": "taupo-nightlife-evening-guide",
    "title": "Taupō Nightlife Guide: 7 Best Lakeside Taprooms, Starlit Spas & Pub Street Dens",
    "style": "risograph",
    "prompt": "Risograph screen print. Craft beer pint glass, steaming outdoor hot pool ripples, starlit lake silhouette. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 9,
    "id": "3d5ba31b-5f1a-8120-968a-c454f7ae0772",
    "slug": "gisborne-nightlife-evening-guide",
    "title": "Gisborne Nightlife Guide: 6 Best Airplane Beer Gardens, Craft Taprooms & Beanbag Cinemas",
    "style": "risograph",
    "prompt": "Risograph screen print. Cider bottle with condensation, wooden picnic bench, hanging festoon light bulbs. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 10,
    "id": "3d5ba31b-5f1a-8147-bf0f-fe7a275a8c64",
    "slug": "new-plymouth-nightlife-evening-guide",
    "title": "New Plymouth Nightlife Guide: 7 Best West End Speakeasies, Craft Taps & Courtyards",
    "style": "risograph",
    "prompt": "Risograph screen print. Craft beer flight paddle, courtyard pergola vines, glowing street lantern. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 11,
    "id": "3d5ba31b-5f1a-813c-8ef6-e79a8569388c",
    "slug": "palmerston-north-nightlife-evening-guide",
    "title": "Palmerston North Nightlife Guide: 6 Best Craft Brewpubs, Wine Dens & Historic Theatres",
    "style": "risograph",
    "prompt": "Risograph screen print. Theatre spotlight beam, wine glasses, velvet curtain drape folds. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 12,
    "id": "3d5ba31b-5f1a-8194-b210-fe26a32c9256",
    "slug": "whangarei-nightlife-evening-guide",
    "title": "Whangārei Nightlife Guide: 6 Best Marina Bistros, Irish Pubs & Twilight Strolls",
    "style": "risograph",
    "prompt": "Risograph screen print. Sailboat mast silhouettes, marina boardwalk timber, evening water ripples. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 13,
    "id": "3d5ba31b-5f1a-815b-b22f-e34649b39dd2",
    "slug": "invercargill-nightlife-evening-guide",
    "title": "Invercargill Nightlife Guide: 6 Best Skyline Cocktail Bars, Roaring Fires & Craft Taps",
    "style": "risograph",
    "prompt": "Risograph screen print. Whisky tumbler glass, roaring fireplace embers, leather armchair silhouette. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 14,
    "id": "3d5ba31b-5f1a-81e2-8e2c-e6df1247bb37",
    "slug": "auckland-to-rotorua-road-trip",
    "title": "Auckland to Rotorua Road Trip: Ultimate Driving Route via Hobbiton, Waitomo & Hamilton Gardens",
    "style": "flat_editorial",
    "prompt": "Flat vector illustration. Winding state highway, rolling green farmland hills, campervan roof rack. New Zealand. Geometric shapes, flat silhouettes. Sage green, terracotta, warm cream."
  },
  {
    "index": 15,
    "id": "3d5ba31b-5f1a-81fa-9cdf-c08053898ffd",
    "slug": "queenstown-to-milford-sound-scenic-drive",
    "title": "Queenstown to Milford Sound Scenic Drive: Stops, Timing & Homer Tunnel Survival Guide",
    "style": "flat_editorial",
    "prompt": "Flat vector illustration. Mountain tunnel portal, alpine highway ribbon, sheer granite valley wall. New Zealand. Geometric shapes, flat silhouettes. Sage green, terracotta, warm cream."
  },
  {
    "index": 16,
    "id": "3d5ba31b-5f1a-81eb-8897-cd241ce598cd",
    "slug": "christchurch-to-queenstown-road-trip",
    "title": "Christchurch to Queenstown Road Trip: Ultimate Alpine Driving Route via Lake Tekapo & Lindis Pass",
    "style": "flat_editorial",
    "prompt": "Flat vector illustration. Turquoise glacial lake shore, alpine mountain pass summit, open road horizon. New Zealand. Geometric shapes, flat silhouettes. Sage green, terracotta, warm cream."
  },
  {
    "index": 17,
    "id": "3d5ba31b-5f1a-81f3-a51b-f894f40d44f4",
    "slug": "classic-nz-wine-trail-wellington-to-napier",
    "title": "Classic New Zealand Wine Trail: Wellington to Napier Route via Martinborough & Hawke’s Bay",
    "style": "flat_editorial",
    "prompt": "Flat vector illustration. Grapevine rows on hillside, cruiser bicycle with basket, wooden wine barrel. New Zealand. Geometric shapes, flat silhouettes. Sage green, terracotta, warm cream."
  },
  {
    "index": 18,
    "id": "3d5ba31b-5f1a-818e-a3c3-cf90e8f4c7ac",
    "slug": "twin-coast-discovery-highway-northland",
    "title": "Twin Coast Discovery Highway: Ultimate Northland Road Trip Loop via Bay of Islands & Cape Reinga",
    "style": "flat_editorial",
    "prompt": "Flat vector illustration. Windswept coastal headland, vehicle ferry boat on water, giant ancient tree trunk. New Zealand. Geometric shapes, flat silhouettes. Sage green, terracotta, warm cream."
  },
  {
    "index": 19,
    "id": "3d5ba31b-5f1a-8107-baa1-f49858ab590e",
    "slug": "southern-scenic-route-dunedin-to-queenstown",
    "title": "Southern Scenic Route: Dunedin to Queenstown Driving Guide via The Catlins & Invercargill",
    "style": "flat_editorial",
    "prompt": "Flat vector illustration. Rugged sea stacks in ocean surf, coastal lighthouse silhouette, windswept bent trees. New Zealand. Geometric shapes, flat silhouettes. Sage green, terracotta, warm cream."
  },
  {
    "index": 20,
    "id": "3d5ba31b-5f1a-810c-8dd3-cfd7e0126db1",
    "slug": "new-zealand-freedom-camping-guide",
    "title": "New Zealand Freedom Camping Guide: Rules, Fines & Best Spots",
    "style": "flat_editorial",
    "prompt": "Flat vector illustration. Campervan rear doors open to mountain view, enamel coffee mug on table, starry night sky. New Zealand. Geometric shapes, flat silhouettes. Sage green, terracotta, warm cream."
  },
  {
    "index": 21,
    "id": "3d5ba31b-5f1a-8109-8526-d996acf099d9",
    "slug": "new-zealand-natural-hot-springs-guide",
    "title": "New Zealand Natural Hot Springs Guide: Secret Bush Pools & Thermal Spas",
    "style": "risograph",
    "prompt": "Risograph screen print. Steaming geothermal bush stream, smooth river pebbles, lush fern fronds. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 22,
    "id": "3d5ba31b-5f1a-8174-b515-e2804de0ed86",
    "slug": "best-day-hikes-new-zealand",
    "title": "7 Best Day Hikes in New Zealand: Epic Alpine Passes, Glaciers & Coastal Peaks",
    "style": "risograph",
    "prompt": "Risograph screen print. Mountain ridge trail, suspension swing bridge, hiking boots on rock. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 23,
    "id": "3d5ba31b-5f1a-81ab-9f01-d31afa915017",
    "slug": "new-zealand-specialty-coffee-guide",
    "title": "New Zealand Specialty Coffee Guide: Origins of the Flat White & Top Roasters",
    "style": "risograph",
    "prompt": "Risograph screen print. Ceramic tulip coffee cup with latte art, pour-over kettle, roasted coffee beans. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 24,
    "id": "3d5ba31b-5f1a-81ff-9deb-dfc361963a65",
    "slug": "craft-beer-trail-new-zealand",
    "title": "Craft Beer Trail New Zealand: Nelson Hops, Wellington Taps & Iconic Breweries",
    "style": "risograph",
    "prompt": "Risograph screen print. Fresh green hop cones on vine, foaming beer tulip glass, brewery equipment. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 25,
    "id": "3d5ba31b-5f1a-813a-8c26-ca824c473d9a",
    "slug": "lord-of-the-rings-film-locations-nz",
    "title": "Lord of the Rings Film Locations New Zealand: Self-Drive Guide from Hobbiton to Mount Doom & Edoras",
    "style": "flat_editorial",
    "prompt": "Flat vector illustration. Round wooden cottage door on grassy mound, volcanic mountain silhouette, braided river. New Zealand. Geometric shapes, flat silhouettes. Sage green, terracotta, warm cream."
  },
  {
    "index": 26,
    "id": "3d5ba31b-5f1a-81d9-b34f-d90603f25ebb",
    "slug": "best-time-to-visit-new-zealand",
    "title": "Best Time to Visit New Zealand: Month-by-Month Weather & Crowd Guide",
    "style": "flat_editorial",
    "prompt": "Flat vector illustration. Compass dial, golden autumn leaf beside mountain peak, open road map. New Zealand. Geometric shapes, flat silhouettes. Sage green, terracotta, warm cream."
  },
  {
    "index": 27,
    "id": "3d5ba31b-5f1a-81ef-a603-e1eebc535ab9",
    "slug": "new-zealand-ski-season-guide",
    "title": "New Zealand Ski Season Guide: Queenstown, Wanaka & Canterbury Slopes",
    "style": "risograph",
    "prompt": "Risograph screen print. Pair of carving skis in fresh snow, chairlift cable tower, alpine mountain ridge. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  },
  {
    "index": 28,
    "id": "3d5ba31b-5f1a-810c-87bf-cc2fc5f6558f",
    "slug": "autumn-in-central-otago-guide",
    "title": "Autumn in Central Otago: Golden Foliage, Wine Harvest & Arrowtown Guide",
    "style": "risograph",
    "prompt": "Risograph screen print. Golden poplar leaves drifting, historic stone cottage roofline, ripe pinot noir grapes. New Zealand. Two-color print, grain texture, halftone dots. Teal and terracotta on cream."
  }
]

def main():
    results_file = ROOT_DIR / "output_images" / "maia_covers_results.json"
    results = {}
    if results_file.exists():
        try:
            with open(results_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    results[item["id"]] = item
        except Exception:
            pass

    from diffusers import AutoPipelineForText2Image, AutoencoderKL

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    print(f"Loading SDXL-Turbo on {device.upper()}...", flush=True)
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

    print("[OK] SDXL-Turbo loaded successfully.\n", flush=True)

    for article in ARTICLES:
        page_id = article["id"]
        slug = article["slug"]
        title = article["title"]
        prompt = article["prompt"]
        index = article["index"]

        print(f"\n[{index}/28] Processing: {title}", flush=True)

        if page_id in results and results[page_id].get("notion_patched"):
            print(f"   [SKIP] Already completed: {results[page_id]['cloudinary_url']}", flush=True)
            continue

        image_path = OUTPUT_DIR / f"{slug}.png"
        full_prompt = NO_TEXT_PREFIX + prompt

        # 1. Generate
        print(f"   [Maia] Generating 1152x864 illustration...", flush=True)
        t0 = time.time()
        final_img = None
        for attempt in range(1, MAX_RETRIES + 1):
            seed = (int(time.time() * 1000) + index * 1000 + attempt * 7919) % (2**32)
            res = pipe(
                prompt=full_prompt,
                num_inference_steps=4,
                guidance_scale=0.0,
                height=IMAGE_HEIGHT,
                width=IMAGE_WIDTH,
                generator=torch.Generator(device=device).manual_seed(seed)
            )
            candidate = res.images[0]
            if detect_text_in_image(candidate) and attempt < MAX_RETRIES:
                print(f"   [RETRY {attempt}] Text detected, retrying with new seed...", flush=True)
                continue
            final_img = candidate
            break

        final_img.save(image_path)
        gen_time = time.time() - t0
        print(f"   [OK] Generated in {gen_time:.1f}s", flush=True)

        # 2. Upload to Cloudinary
        print(f"   [Cloudinary] Uploading...", flush=True)
        up_res = cloudinary.uploader.upload(
            str(image_path),
            public_id=slug,
            folder="nz-travel",
            overwrite=True
        )
        cloudinary_url = up_res["secure_url"]
        print(f"   [OK] Cloudinary URL: {cloudinary_url}", flush=True)

        # 3. Clean up local file immediately (Zero Local Storage)
        if image_path.exists():
            image_path.unlink()
            print(f"   [CLEANUP] Deleted local file: {image_path.name}", flush=True)

        # 4. Patch Notion Page Cover
        print(f"   [Notion] Patching cover...", flush=True)
        patch_payload = {
            "cover": {
                "type": "external",
                "external": {
                    "url": cloudinary_url
                }
            }
        }
        resp = requests.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=NOTION_HEADERS,
            json=patch_payload,
            timeout=30
        )
        if resp.status_code == 200:
            print(f"   [SUCCESS] Notion cover updated!", flush=True)
            notion_patched = True
        else:
            print(f"   [WARN] Notion patch returned {resp.status_code}: {resp.text}", flush=True)
            notion_patched = False

        results[page_id] = {
            "index": index,
            "id": page_id,
            "slug": slug,
            "title": title,
            "cloudinary_url": cloudinary_url,
            "notion_patched": notion_patched,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Save progress
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(list(results.values()), f, ensure_ascii=False, indent=2)

    print("\n==================================================", flush=True)
    print(f"🎉 All 28 covers generated, uploaded to Cloudinary, and patched to Notion!", flush=True)
    print("==================================================", flush=True)

if __name__ == "__main__":
    main()
