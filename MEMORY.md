# MEMORY.md - Long-Term Memory

## About Alperen
- **Name:** Alperen K.
- **Username:** @alprnkmbr (Telegram)
- **Timezone:** Europe/Istanbul (GMT+3)
- **Language:** Turkish (primary), English (fluent)
- **Communication style:** Direct, no fluff. Prefers concise answers.

## Working Rules (CRITICAL)
- **NEVER make code changes without Alperen's explicit permission.** One change at a time, only when asked.
- **Don't over-engineer.** The existing systems mostly work — incremental improvements over rewrites.
- **Ask before acting externally** (emails, tweets, public posts).
- **Turkish context:** Briefs and content are in Turkish. Video bot headlines are rewritten for clarity.

## Projects

### Frontion News Bot (Video)
- **Path:** `/Users/claudius/frontion-bot/bot.py`
- **YouTube:** `@FrontionNewsBot`
- **Pipeline:** RSS feed → headline → image search → video frame generation → upload
- **Known issues (2026-06-29):** Image search quality, center crop can cut faces, title text readability, harsh overlay transition, static video
- **Important:** Original image search was ~99% accurate. Don't break it trying to "improve."
- **Headline rewriting:** Bot rewrites RSS headlines for video frames (exists somewhere in code, not found yet)

### LinkedIn Brief Pipeline
- **Path:** `/Users/claudius/clawd/frontion-site/`
- **Scripts:** `linkedin_post.py`, `linkedin_cards.py`
- **Briefs:** `briefs/`, `defense/`, `energy/`, `turkey/`
- **Global brief schedule:** BLUF 7:30, S1-S6 every 30 min, Bottom Line 11:00
- **Defence brief schedule:** BLUF 14:00, S1-S7 every 30 min, Bottom Line 18:00
- **Model:** `ollama/glm-5.1:cloud`, isolated session, 120s timeout
- **Make.com:** Was deactivated due to 404 errors (image URL not deployed when webhook called). Increased `wait_for_url` to 60s.

### Frontion Website (frontion.news)
- **Path:** `/Users/claudius/clawd/frontion-site/`
- **Hosted on:** GitHub Pages (alprnkmbr.github.io/frontion-news)
- **Main page:** `index.html` — geopolitical brief aggregator
- **Briefs:** Global (`briefs/`), Defence (`defense/`), Energy (`energy/`), Finance (`finance/`), Tech (`tech/`), Turkey (`turkey/`)
- **Turkey brief:** Hidden from main site dropdown, accessible at `frontion.news/turkey`, `noindex` meta tag
- **RSS feed:** `feed.xml` — auto-generated
- **Landing mockup:** `mockup-landing.html` — hero + 4 category headings, light theme default
- **Other pages:** `brief.html`, `archive.html`, `turkey.html`
- **Scripts:** `add_news.py`, `gen_rss.py`, `generate_brief_feed.py`, `generate_feed.py`, `update_headlines.py`, `update_tier2.py`, `publish-brief.py`
- **Weekly email:** `send_weekly_email.py`
- **LinkedIn scheduling:** `linkedin_schedule.py` — auto-creates cron jobs based on section count

## Editorial Policy (CRITICAL)
- **Frontion News was founded to counter orientalist/imperialist perspectives on Turkey.**
- Turkey-specific content is not published as a separate section, but Turkey-related news in any brief must be covered objectively — never from an orientalist, anti-Turkish, or Western-hegemonic lens.
- **Contested historical/political topics** (e.g., Armenian genocide claims, Kurdish issues, Cyprus, etc.) must use **neutral, non-partisan language**. Never frame one side's narrative as established truth. Use phrasing like "contested narrative," "disputed claims," "widely debated," etc.
- **No value judgments** on sovereignty disputes, territorial claims, or national narratives. Report what happened and what it means — not whose side is "right."
- This applies to ALL briefs (Global, Defence, Energy, Tech, Finance, Turkey) and ALL outputs (website, LinkedIn, video descriptions, etc.)

## Lessons Learned
- **2026-06-30:** Turkey brief used "historical truth" for Armenian genocide recognition — corrected to "a contested historical narrative." Always use neutral language on disputed topics.
- **2026-06-29:** Attempted to improve bot image quality with scoring/saliency — all reverted at Alperen's request. Original code worked fine. Don't over-engineer.
- **2026-06-29:** Always confirm changes before implementing. No unsolicited modifications.
- **MEMORY.md must exist.** Without it, context is lost between sessions.

## Preferences
- Prefers `trash` over `rm` (recoverable)
- Works in Turkish for content, English for code/technical
- Values stability over novelty in production systems