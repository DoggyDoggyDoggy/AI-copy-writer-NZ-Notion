# Template: Food, Coffee & Drink Guide

## Notion Properties Pattern:
```yaml
Title: "Where to Eat in [City Name]: Best Cafes, Local Kai & Craft Breweries"
Slug: "[city-slug]-best-food-cafes-restaurants"
Description : "Discover where to eat and drink in [City Name]. From award-winning flat whites to ocean-fresh seafood and craft breweries, here is your foodie guide."
City: "[city-slug]"
Tags: ["[city-slug]", "food-and-drink", "cafes", "restaurants"]
Date: null    # ← ALWAYS null on creation. User sets date manually in Notion.
Published: false  # ← STRICT: ALWAYS false. Never set to true. User toggles manually in Notion.
Featured: false
# WORD COUNT: Target 1500–2000 words IF data is rich. Write shorter if verified content is scarce — no padding.
```

---

## ⚙️ Tier Adaptation Rule (READ BEFORE WRITING)

> **Check the city's Tier in `cities/[city-slug].md` before deciding on structure.**

| City Tier | Structure Approach |
|---|---|
| **Tier 1** (Auckland, Wellington, Christchurch, Queenstown) | Use ALL sections below. 3+ venues per section. Full tasting notes. |
| **Tier 2** (Rotorua, Napier, Dunedin, Hamilton, etc.) | Use 3–4 sections. 2–3 venues per section. Merge thin sections. |
| **Tier 3** (Invercargill, Gisborne, Whangārei, Palmerston North) | Collapse into 2 sections max: **"Best Local Kai" + "Drinks & Atmosphere"**. 4–5 deeply described venues total. Do NOT split into Coffee / Lunch / Dinner / Brewery just to fill space. |

---

## Article Content Structure:
```markdown
# Where to Eat in [City Name]: The Ultimate Local Food & Coffee Guide

[Introduction celebrating the region's culinary identity, local ingredients, and coffee culture.]

---

## Best Coffee & Morning Bakeries
[Tier 1–2: 3 specific roasters / cafes with signature pastry & coffee recommendations.
 Tier 3: Combine with Casual Lunch below if fewer than 2 genuine specialty cafes exist.]

---

## Casual Lunch & Iconic Kiwi Bites
[Fish & chips, sourdough toasties, gourmet pies, farmers markets.]

---

## Top Dinner Spots & Regional Dining
[Locally sourced seafood, grass-fed beef/lamb, wine pairings.
 Tier 3: Only include if verified dinner venues exist — never invent.]

---

## Craft Breweries & Wine Cellar Doors
[Tier 1–2: Local taprooms, cideries, or nearby cellar doors.
 Tier 3: Skip this section entirely if no genuine brewery/cellar door exists in town.]

---

## Foodie Map & Quick Reference
| Spot | Best For | Neighbourhood | Price Range |
|---|---|---|---|
| [Name] | [Specialty] | [Suburb] | [$ / $$ / $$$] |

---

## Eating in [City Name]: A Few Honest Questions Answered

> Natural, helpful close. Reads like insider advice, not a keyword block.
> 3 questions. Each answer: 50–80 words. Specific to this city's dining reality.

**What is [City Name] most famous for food-wise?**
[One specific, honest answer. A signature dish, ingredient, or regional specialty — not "great food scene". E.g. Bluff oysters, Hawke's Bay Chardonnay, Gisborne Chardonnay, Invercargill cheese rolls.]

**Is [City Name] good for vegetarians / vegans?**
[Honest and specific — name 1–2 venues that genuinely cater well. For Tier 3: be honest if options are limited.]

**What's the average cost of eating out in [City Name]?**
[Give a realistic NZD range for: cafe breakfast ($), casual lunch ($$), sit-down dinner ($$$). Compare to NZ average if notably cheaper or more expensive.]
```
