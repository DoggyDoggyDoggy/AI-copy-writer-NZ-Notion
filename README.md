# 🇳🇿 NZ Travel Guide — AI Content Engine

A modular, multi-persona AI content engine for researching, drafting, rewriting, fact-checking, and editorially critiquing high-ranking New Zealand destination guides and travel articles.

---

## 📁 Repository Structure

```
├── .antigravityrules              # Core instructions, standards, and 6-stage pipeline
├── .env.example                   # Environment variable template (copy to .env)
├── README.md                      # System manual & operational guide
├── personas/                      # Complete 6-Stage Personas Suite
│   ├── researcher.md                    # Stage 1: Kiri (Live web scout & deep fact-finder)
│   ├── copywriter_local_explorer.md     # Stage 2: Liam (Hikes, nature, outdoor adrenaline)
│   ├── copywriter_urban_foodie.md       # Stage 2: Aroha (Dining, coffee, art, culture)
│   ├── copywriter_savvy_roadtripper.md  # Stage 2: Dave (Itineraries, budget, road logistics)
│   ├── rewriter_deep_synthesizer.md     # Stage 2: Tui (Deep synthesis & originality)
│   ├── rewriter_angle_pivot.md          # Stage 2: Tama (Angle/vector/conclusion pivot)
│   ├── fact_checker.md                  # Stage 3: Sam (Ground-truth auditor & verifier)
│   ├── critic.md                        # Stage 4: Morgan (Style critic, anti-slop & SEO editor)
│   ├── notion_publisher.md              # Stage 5: Tane (Safe Notion database draft ingestion)
│   └── image_designer.md               # Stage 6: Maia (Visual designer & cover image generator)
├── scripts/                       # Image generation scripts & ComfyUI workflows
│   ├── generate_image.py                # Main image generation + Cloudinary upload script
│   ├── comfyui_setup.md                 # Step-by-step ComfyUI setup guide
│   └── comfyui_workflows/
│       ├── sdxl_turbo_flat_editorial.json  # Workflow: Flat Editorial style
│       └── sdxl_turbo_risograph.json       # Workflow: Risograph print style
├── templates/                     # Dynamic templates per content format
│   ├── article_schema.md                # Schema overview & dynamic metadata rules
│   ├── pillar_guide.md                  # Comprehensive City Pillar Guide
│   ├── top_things_to_do.md              # Numbered "Best Things to Do" Listicle
│   ├── itinerary.md                     # Step-by-Step 1/3/7-Day Itineraries
│   ├── food_and_drink.md                # Cafes, Roasters & Dining Trails
│   └── budget_practical.md             # Free Sights & Budget Hacks
└── cities/                        # Factual profiles for all 15 cities
    ├── auckland.md
    ├── christchurch.md
    ├── dunedin.md
    ├── gisborne.md
    ├── hamilton.md
    ├── invercargill.md
    ├── napier.md
    ├── new-plymouth.md
    ├── palmerston-north.md
    ├── queenstown.md
    ├── rotorua.md
    ├── taupo.md
    ├── tauranga.md
    ├── wellington.md
    └── whangarei.md
```

---

## 🌐 Language Protocol: 100% English Engine
* **User Input**: You can write prompts or speak in **Russian** (or any language).
* **Under-the-Hood Operations (Strictly English)**:
  - **Live Web Research**: Search queries and dossiers are generated in **100% English**.
  - **Copywriting / Rewriting**: All prose, headings, and metadata are crafted in **100% New Zealand English**.
  - **Fact-Checking & Critique**: Verification queries, audit reports, and final Markdown are **100% English**.
  - **Notion Database**: Staged properties (`Title`, `Slug`, `Description `) and article body are stored **100% in English**.
* **Chat Output**: Antigravity reports back and chats with you in your language of choice.

---

## 🎭 The Personas Suite

### 🔍 Stage 1: Researcher Persona
| Persona | Name | Role | Capabilities |
|---|---|---|---|
| **Researcher** | **Kiri** | Live Web Scout & Fact-Finder | Searches live internet for specific topics, extracts real venue names, exact street addresses, signature menu items/trails, opening hours, prices, and builds a verified Research Dossier. |

### ✍️ Stage 2: 3 Copywriter Personas
| Persona | Name | Focus | Style & Vibe |
|---|---|---|---|
| **Copywriter 1** | **Liam** | Outdoor, Hiking, Nature | Rugged, adventurous, secret trails, surf & coastal spots |
| **Copywriter 2** | **Aroha** | Urban Culture & Food | Specialty coffee roasters, local kai, art galleries, heritage |
| **Copywriter 3** | **Dave** | Roadtrips & Budget | Practical road advice, family-friendly, campervan tips, costs |

### 🔄 Stage 2 Alternative: 2 Rewriter Personas
| Persona | Name | Focus | Purpose & Capabilities |
|---|---|---|---|
| **Rewriter 1** | **Tui** | Deep Synthesizer | Takes 1+ source URLs/articles, strips duplicate structure, synthesizes into 100% original Kiwi copy with high burstiness & E-E-A-T. |
| **Rewriter 2** | **Tama** | Angle Pivot Specialist | Takes existing articles or links and completely pivots the angle (e.g. Luxury $\to$ Campervan; General $\to$ 48-Hour Foodie Itinerary; Standard $\to$ Hidden Spots). |

### 🛡️ Stage 3: Fact-Checker Persona
| Persona | Name | Role | Capabilities |
|---|---|---|---|
| **Fact-Checker** | **Sam** | Ground-Truth Auditor & Verifier | Scans draft articles, audits claims against live web sources, corrects factual errors in place, and produces a Fact-Check Report + verified article. |

### 🖋️ Stage 4: Critic Persona
| Persona | Name | Role | Capabilities |
|---|---|---|---|
| **Critic & Editor** | **Morgan** | Style Critic, Anti-Slop & SEO Master | Scrubs AI clichés/slop, optimizes readability and sentence cadence, upgrades headers for SEO/clicks, and finalizes pristine Markdown. |

### 📡 Stage 5: Notion Publisher Persona
| Persona | Name | Role | Capabilities |
|---|---|---|---|
| **Notion Publisher** | **Tane** | Safe Database Ingestion Engine | Creates new draft entries in Notion (`database_id: 3bbba31b...bfc92`), populates properties, sets `Published: false` & `Date: empty` for safe staging, and uploads full Markdown. |

### 🎨 Stage 6: Visual Designer Persona
| Persona | Name | Role | Capabilities |
|---|---|---|---|
| **Visual Designer** | **Maia** | Cover Image Generator | Reads the finished article, extracts visual themes, builds a brand-locked prompt (2 styles: Flat Editorial / Risograph), generates 1024×1024 PNG locally via ComfyUI + SDXL-Turbo, uploads to Cloudinary, and patches the Notion page cover with the URL. Palette locked to Sage (#4A7C72) + Terracotta (#C4623A). Zero photorealism, zero landmarks, zero faces. |

---

## 🛡️ Anti-AI Detection & Google E-E-A-T Standards

All copywriters maintain their unique voice while strictly implementing the dual-engine quality framework:

1. **AI Detector Bypass Engine (Burstiness & Perplexity)**:
   - **Sentence Burstiness**: Mixes ultra-short punchy fragments (2–5 words), standard descriptive clauses (12–18 words), and complex, sensory multi-clause sentences (28–42 words with dashes).
   - **High Perplexity**: Eliminates predictable AI phrases (*"Whether you are..."*, *"In conclusion..."*, *"Furthermore"*); replaces them with natural conversational turns (*"Here's the catch:"*, *"Truth be told,"*).
   - **Zero AI Cliché Policy**: Complete ban on *nestled, tapestry, testament to, beacon, haven, embark, delve, boast, picturesque, myriad*.

2. **Google E-E-A-T Engine (Experience, Expertise, Authority, Trust)**:
   - **Lived Experience**: Tactile sensory details (spray of waterfalls, coffee crema, mountain pass chill).
   - **Critical Honesty**: Balanced reviews with real-world trade-offs (parking capacity, steep climbs, sandflies, mobile dead-zones).
   - **Authentic Te Reo Māori**: Contextual use of *Manaakitanga, Kai, Whenua, Moana, Hikoi, Whānau*.

---

## ⚡ The 5-Stage Pipeline Workflow

Every content generation request automatically follows five stages:

1. **Stage 1 (Researcher / Kiri)**:
   - Conducts live web research via search tools for active places, real addresses, signature items, and local nuances.
   - Compiles a structured **Research Dossier**.

2. **Stage 2 (Copywriter / Aroha, Liam, Dave)**:
   - Ingests the Research Dossier + City Profile + Template.
   - Writes rich, authentic, anti-slop copy in the chosen persona voice while executing burstiness and E-E-A-T rules.

3. **Stage 3 (Fact-Checker / Sam)**:
   - Audits all factual statements, venue names, addresses, and hours against live web search results.
   - Corrects any inaccuracies directly in the text and outputs the verified version.

4. **Stage 4 (Critic & Editor / Morgan)**:
   - Eliminates AI tropes/clichés, verifies burstiness and E-E-A-T anchors, refines H2/H3 headers for SEO, and formats into final, publish-ready Markdown with an Editorial Report.

5. **Stage 5 (Notion Publisher / Tane)**:
   - Ingests the article into Notion Database `NZ Travel Articles`.
   - **Safe Staging**: Sets `Published = false` and `Date = [Unset]` so nothing goes live automatically on your website.
   - You review the draft in Notion, check `Published`, and pick your release date.

---

## 💡 How to Use (Examples)

You can prompt Antigravity with simple, natural instructions right here in this chat:

### Example 1: General Request (Interactive Persona Selection)
> **User**: *"Напиши статью про Гамильтон"* (или *"Напиши 3 статьи для трех городов"*).
> 
> **Antigravity**: Если автор не был указан в промпте, я сначала спрошу вас:
> * «Какого автора вы хотите назначить?»
>   1. 🧗‍♂️ **Liam (Local Explorer)** — Походы, трекинг, дикая природа, серфинг, секретные смотровые площадки.
>   2. ☕ **Aroha (Urban Foodie)** — Спешелти кофе, рестораны, гастрономия, культура маори (*Manaakitanga*).
>   3. 🚐 **Dave (Savvy Roadtripper)** — Автопутешествия, кемперваны, бюджетные лайфхаки, логистика.
> 
> Вы выбираете автора (или указываете разных авторов для разных городов), и запускается полный 5-этапный конвейер.

### Example 2: Direct Request with Chosen Persona (Immediate Execution)
> **User**: *"Напиши статью про лучшие кафе в Гамильтоне через Ароху."*
> 
> **Pipeline Execution**:
> 1. **Researcher (Kiri)**: Ищет актуальные спешелти-кофейни и бранч-споты в Гамильтоне (100% на английском).
> 2. **Aroha (Urban Foodie)**: Пишет черновик с высоким Perplexity/Burstiness и E-E-A-T.
> 3. **Fact-Checker (Sam)**: Проверяет адреса, часы работы и меню, вносит точечные правки.
> 4. **Critic (Morgan)**: Удаляет AI-клише, шлифует ритм текста, оптимизирует SEO H2/H3.
> 5. **Notion Publisher (Tane)**: Загружает черновик в Notion (`Published = false`, `Date = [Unset]`) и возвращает вам ссылку.

### Example 3: Adventure & Hiking Guide (Direct execution)
> **User**: *"Напиши путеводитель по однодневным трекам вокруг Квинстауна. Используй персону Liam."*
> 
> **Pipeline Execution**:
> 1. **Researcher (Kiri)** searches the web for current DOC track statuses, elevation gain, trailheads, and warnings.
> 2. **Liam (Local Explorer)** writes an energetic, trail-tested guide.
> 3. **Fact-Checker (Sam)** verifies trail distances, DOC facilities, and safety guidelines.
> 4. **Critic (Morgan)** strengthens readability, formats callout warnings, and delivers polished Markdown.
> 5. **Notion Publisher (Tane)** creates the draft page in Notion ready for your manual date assignment.

### Example 4: Deep Rewrite & Narrative Pivot from Source URLs (Track B)
> **User**: *"Вот ссылка [URL]. Перепиши статью."*
> 
> **Antigravity**: Спрашивает:
> * «Какого рерайтера назначить?»
>   1. 📚 **Tui (The Deep Synthesizer)** — Комплексный фундаментальный гид.
>   2. 🔀 **Tama (The Angle Pivot Specialist)** — Кардинальная смена угла (например, в бюджетный кемперван-трип).
> 
> После вашего ответа материал проходит рерайт, фактчекинг Сэмом, редактуру Морганом и сохраняется черновиком в Notion.
> 
> *Behavior*:
> 1. **Stage 1 skipped**: Source URLs are provided directly.
> 2. **Tama (Angle Pivot Specialist)** deconstructs the source facts, drops the luxury spa focus, injects free natural hot pools (Kerosene Creek, Secret Spot hacks) and freedom camping rules using high burstiness and E-E-A-T.
> 3. **Fact-Checker (Sam)** verifies all road access, current council freedom camping bylaws, and parking fees.
> 4. **Critic (Morgan)** scrubs AI tropes, polishes flow and SEO headlines, and formats Markdown.
> 5. **Notion Publisher (Tane)** stages the draft into Notion (`Published: false`, `Date: [Unset]`) and provides the link.



