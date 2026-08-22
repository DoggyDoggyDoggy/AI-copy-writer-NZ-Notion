# ⚙️ ComfyUI Setup Guide — Maia Image Generation

## Что такое ComfyUI?

ComfyUI — это локальный движок для генерации изображений через Stable Diffusion. Maia (Stage 6) подключается к нему через REST API и отправляет запросы автоматически. **Тебе не нужно вручную работать с ComfyUI** — нужно только запустить его как фоновый сервер.

---

## 📍 Шаг 1 — Найди папку ComfyUI

ComfyUI уже установлен на твоём компьютере. Найди папку — обычно это:
- `C:\ComfyUI\`
- `C:\Users\[имя]\ComfyUI\`
- Или там, куда ты его устанавливал

Внутри папки должен быть файл `main.py`.

---

## 📦 Шаг 2 — Скачать модель SDXL-Turbo

Maia использует **SDXL-Turbo** — быструю модель (2–5 сек на картинку, 8GB VRAM).

### Скачать через ComfyUI Manager (рекомендую):
1. Запусти ComfyUI (см. Шаг 3)
2. В интерфейсе нажми **Manager** → **Install Models**
3. Найди `sd_xl_turbo_1.0_fp16` → **Install**

### Скачать вручную (альтернатива):
1. Скачай файл с HuggingFace:  
   **[sd_xl_turbo_1.0_fp16.safetensors](https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors)**  
   (Размер: ~6.9 GB)
2. Положи файл в папку:  
   `ComfyUI\models\checkpoints\sd_xl_turbo_1.0_fp16.safetensors`

---

## 🚀 Шаг 3 — Запустить ComfyUI как API-сервер

Открой терминал (PowerShell или CMD) в папке ComfyUI и выполни:

```powershell
python main.py --listen
```

Флаг `--listen` важен — он разрешает внешние подключения от Maia.

**Ожидаемый вывод в терминале:**
```
Starting server

To see the GUI go to: http://127.0.0.1:8188
```

ComfyUI теперь работает как фоновый сервер на `http://localhost:8188`.

> **⚠️ Важно**: ComfyUI должен быть запущен КАЖДЫЙ РАЗ перед использованием Maia.  
> Оставь окно терминала открытым — закрытие терминала остановит сервер.

---

## ✅ Шаг 4 — Проверить подключение

После запуска ComfyUI, проверь подключение через Maia:

```powershell
cd f:\vibe_coding_projects\AI-copy-writer-NZ-Notion
python scripts/generate_image.py --check
```

Ожидаемый вывод:
```
✅ ComfyUI запущен и отвечает
```

---

## 🔧 Шаг 5 — Настроить переменные окружения (.env)

Скопируй файл `.env.example` в `.env` и заполни:

```powershell
Copy-Item .env.example .env
```

Затем открой `.env` и вставь свои ключи Cloudinary (см. ниже).

---

## ☁️ Шаг 6 — Создать аккаунт Cloudinary

1. Иди на **[cloudinary.com](https://cloudinary.com)** → **Sign Up Free**
2. После регистрации открой **Dashboard**
3. Скопируй три значения:
   - **Cloud Name** (`your_cloud_name`)
   - **API Key** (`your_api_key`)
   - **API Secret** (`your_api_secret`)
4. Вставь их в файл `.env`

---

## 📁 Структура папок после настройки

```
AI-copy-writer-NZ-Notion/
├── .env                          ← твои секреты (НЕ в git)
├── .env.example                  ← шаблон (в git)
├── personas/
│   └── image_designer.md         ← персона Maia (Stage 6)
├── scripts/
│   ├── generate_image.py         ← основной скрипт
│   └── comfyui_workflows/
│       ├── sdxl_turbo_flat_editorial.json
│       └── sdxl_turbo_risograph.json
└── output_images/                ← временные файлы (auto-created, не в git)
```

---

## 🔄 Типичный рабочий процесс

```
1. Запусти ComfyUI: python main.py --listen  (в папке ComfyUI)
2. Напиши новую статью через Antigravity IDE как обычно
3. После Stage 5 (Tane) → Maia автоматически запускается
4. Maia показывает промпт → ты одобряешь
5. Картинка генерируется → загружается в Cloudinary → ссылка в Notion
```

---

## ❓ Частые проблемы

| Проблема | Решение |
|---|---|
| `❌ ComfyUI не запущен` | Запусти `python main.py --listen` в папке ComfyUI |
| `Model not found` | Скачай `sd_xl_turbo_1.0_fp16.safetensors` в `models/checkpoints/` |
| `CUDA out of memory` | Добавь флаг `--lowvram` к команде запуска |
| `Cloudinary upload failed` | Проверь ключи в `.env` файле |

### Запуск с меньшим VRAM (если ошибка памяти):
```powershell
python main.py --listen --lowvram
```

---

## 📌 Быстрый старт (шпаргалка)

```powershell
# Каждый раз перед работой с Maia:
cd C:\ComfyUI          # замени на свой путь к ComfyUI
python main.py --listen

# В другом терминале — проверка:
cd f:\vibe_coding_projects\AI-copy-writer-NZ-Notion
python scripts/generate_image.py --check
```
