# Maia Setup Guide — Local Image Generation (No ComfyUI)

## Как это работает

Maia использует библиотеку `diffusers` для запуска **SDXL-Turbo** прямо из Python.  
**Никаких отдельных программ не нужно** — модель скачивается автоматически с HuggingFace при первом запуске (~6.9 GB) и кэшируется на диске.

**Твой GPU**: NVIDIA RTX 3070 (8 GB VRAM) — работает идеально.

---

## Зависимости (уже установлены)

Проверено на твоей системе:
- `torch 2.13.0` — CUDA поддержка
- `diffusers 0.39.0` — загрузка и запуск SDXL-Turbo
- `transformers 5.15.0` — токенизаторы
- `accelerate 1.14.0` — оптимизация памяти

---

## Шаг 1 — Настроить Cloudinary

1. Иди на **[cloudinary.com](https://cloudinary.com)** → **Sign Up Free**
2. После регистрации открой **Dashboard**
3. Скопируй три значения:
   - **Cloud Name**
   - **API Key**
   - **API Secret**

---

## Шаг 2 — Создать .env файл

```powershell
cd f:\vibe_coding_projects\AI-copy-writer-NZ-Notion
Copy-Item .env.example .env
```

Открой `.env` и заполни:

```
CLOUDINARY_CLOUD_NAME=your_cloud_name_here
CLOUDINARY_API_KEY=your_api_key_here
CLOUDINARY_API_SECRET=your_api_secret_here
```

---

## Шаг 3 — Проверить GPU

```powershell
python scripts/generate_image.py --check
```

Ожидаемый вывод:
```
[OK] GPU: NVIDIA GeForce RTX 3070 (8.0 GB VRAM) - CUDA
```

---

## Шаг 4 — Тестовая генерация

При первом запуске модель скачается (~6.9 GB). Последующие запуски — мгновенно из кэша.

```powershell
python scripts/generate_image.py `
  --style flat_editorial `
  --prompt "Flat editorial travel poster illustration. Best cafes in Auckland, New Zealand. Minimal geometric shapes, bold silhouettes. Color palette: sage green, terracotta, warm cream. No photorealism, no faces, no text, no landmarks. Style: Monocle magazine cover, mid-century modern. Subjects: espresso cup, harbour view, bicycle, fern leaf." `
  --slug "test-auckland-cafes"
```

---

## Процесс генерации

```
1. GPU загружает модель SDXL-Turbo из кэша (~2-3 сек)
2. Генерация 1024x1024 PNG (4 шага, ~5-15 сек на RTX 3070)
3. Сохраняет в output_images/test-auckland-cafes.png
4. Загружает в Cloudinary
5. Возвращает URL для Notion
```

---

## Как Maia запускается из Antigravity

Когда ты пишешь статью и говоришь Maia сгенерировать обложку, Maia:

1. Читает статью из Notion
2. Выбирает стиль (Flat Editorial или Risograph)
3. Составляет промпт из шаблона
4. Показывает тебе промпт и спрашивает: `"Запускаем? (да / изменить промпт)"`
5. Запускает: `python scripts/generate_image.py --style ... --prompt "..." --slug "..."`
6. Показывает путь к PNG → ты можешь открыть и посмотреть
7. Загружает в Cloudinary → вставляет URL в Notion как Cover

---

## Кэш модели

Модель хранится в: `C:\Users\[имя]\.cache\huggingface\hub\`  
Размер: ~6.9 GB  
После первой загрузки — больше не скачивается.

---

## Быстрый старт (шпаргалка)

```powershell
# Проверить GPU:
python scripts/generate_image.py --check

# Сгенерировать картинку:
python scripts/generate_image.py --style flat_editorial --prompt "..." --slug "my-article"

# Загрузить готовую картинку в Cloudinary:
python scripts/generate_image.py --upload output_images/my-image.png --slug "my-article"
```
