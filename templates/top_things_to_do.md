# Template: Top Things to Do (Listicle)

## Notion Properties Pattern:
```yaml
Title: "[X] Best Things to Do in [City Name]: Must-See Sights & Hidden Gems"
Slug: "[city-slug]-best-things-to-do"
Description : "Looking for the top things to do in [City Name]? From iconic landmarks to local secret spots, here are [X] unmissable experiences."
City: "[city-slug]"
Tags: ["[city-slug]", "things-to-do", "activities", "[north-island|south-island]"]
Date: null    # ← ALWAYS null on creation. User sets date manually in Notion.
Published: false  # ← STRICT: ALWAYS false. Never set to true. User toggles manually in Notion.
Featured: false
# WORD COUNT: Target 1500–2000 words IF data is rich. Write shorter if verified content is scarce — no padding.
```

---

## ⚙️ Tier Adaptation Rule (READ BEFORE WRITING)

> **Check the city's Tier in `cities/[city-slug].md` before deciding how many items to list.**

| City Tier | Number of Items | Approach |
|---|---|---|
| **Tier 1** (Auckland, Wellington, Christchurch, Queenstown) | 10–15 items | Each entry 150–200 words. Full variety across activity types. |
| **Tier 2** (Rotorua, Napier, Dunedin, Hamilton, etc.) | 7–10 items | Each entry 150–200 words. Focus on the city's defining theme. |
| **Tier 3** (Invercargill, Gisborne, Whangārei, Palmerston North) | 5–7 items | Each entry 200–250 words (deeper focus per item). Include surrounding day-trip spokes as legitimate entries — do NOT pad with thin in-town activities. |

---

## Article Content Structure:
```markdown
# [X] Best Things to Do in [City Name]: The Local's Checklist

[Vibrant 2-paragraph introduction. Cut straight to why this destination has experiences worth knowing.]

---

### 1. [Top Landmark / Iconic Attraction]
- **Location**: [Exact street or reserve name]
- **Cost**: [Free / $XX NZD]
- **The Experience**: [Vivid description of what makes it great]
- **Local Insider Tip**: [Where to park, best lighting for photos, skip-the-line advice]

### 2. [Scenic Nature Walk / Viewpoint]
...
### 3. [Cultural or Heritage Experience]
...
### 4. [Active Adventure / Water Activity]
...
### 5. [Off-the-Beaten-Track Secret]
...

[Tier 3 cities: items 6–7 may be day-trip spokes within 45 mins drive — these count as legitimate experiences]

---

## Pro-Tips for Visiting [City Name]'s Attractions
> **Local Tip**: [Specific actionable insight on weather or ticketing].

---

## Before You Go: [City Name] Quick Answers

> Warm, conversational heading — NOT "FAQ". Reads like a local friend briefing you.
> 3 questions max for listicle format. Each answer: 40–70 words. Sharp and specific.

**Is [City Name] worth a full day / two days?**
[Honest time-budget answer linked to specific items in the list above.]

**What's the one thing you absolutely shouldn't miss in [City Name]?**
[Pick the single standout from the list. Give a genuine opinion — not "everything is great".]

**Do I need to book in advance for [specific attraction]?**
[Practical booking reality: peak season, walk-in viability, booking links if relevant.]
```
