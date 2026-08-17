# Article Schema & Dynamic Generation Framework

This document outlines how article properties (Title, Slug, Description, Tags) and content structures dynamically adapt based on the **Content Type** and **Topic**.

---

## 🎯 Dynamic Notion Properties Formula

Instead of a static template, each article's properties are generated dynamically:

| Notion Property | Generation Rule & Formula | Examples |
|---|---|---|
| **`Title`** | `[Punchy Hook / Number] + [Target City/Region] + [Specific Topic / Angle]` | • *"12 Best Things to Do in Napier: Art Deco, Wine & Coastal Trails"*\n• *"Where to Eat in Dunedin: Best Cafes, Student Bites & Breweries"*\n• *"3 Days in Queenstown: The Ultimate Adventure & Wine Itinerary"* |
| **`Slug`** | Lowercase, hyphenated, clean URL slug derived from topic | • `napier-best-things-to-do`\n• `dunedin-food-guide-best-cafes`\n• `queenstown-3-day-itinerary` |
| **`Description `** | 140–160 char meta description containing key search intent + local hook *(Note the trailing space in property name)* | • *"Discover the top 12 things to do in Napier, from historic 1930s Art Deco walking tours to biking scenic Hawke's Bay winery trails."* |
| **`City`** | Exact lowercase city slug matching the 15 supported cities | `auckland`, `queenstown`, `wellington`, `napier`, `dunedin`, etc. |
| **`Tags`** | 3–5 multi-select tags: `[city, article-type, island, specific-theme]` | `["napier", "things-to-do", "north-island", "wine"]` |
| **`Date`** | Left `null` / empty on initial ingestion so the user selects their preferred publication date manually in Notion | `null` (Manual Selection in Notion) |
| **`Published`** | **STRICTLY `false`** (Unchecked draft mode to prevent automatic website deployment) | `false` |
| **`Featured`** | Checkbox boolean (`true` for cornerstone/pillar city guides, `false` for sub-topics) | `false` |

---

## 📚 Supported Article Content Types & Schemas

### 1. Pillar City Guide (Comprehensive Overview)
* **File**: `templates/pillar_guide.md`
* **Focus**: Full destination guide covering highlights, neighborhoods, food, timing, and transport.
* **Featured**: `true`

### 2. "Top X / Things to Do" Listicle
* **File**: `templates/top_things_to_do.md`
* **Focus**: Curated numbered activities with insider tips, booking advice, and practical anchors.
* **Featured**: `false`

### 3. Itinerary Guide (1-Day, 3-Day, Weekend, 7-Day)
* **File**: `templates/itinerary.md`
* **Focus**: Chronological, step-by-step route planning with realistic drive times and stops.
* **Featured**: `false`

### 4. Food, Coffee & Nightlife Guide
* **File**: `templates/food_and_drink.md`
* **Focus**: Best cafes, specialty roasters, farm-to-table dining, craft breweries, and local markets.
* **Featured**: `false`

### 5. Budget, Practical & Off-Season Guide
* **File**: `templates/budget_practical.md`
* **Focus**: Free attractions, budget hacks, camping/holiday parks, weather reality, road safety.
* **Featured**: `false`
