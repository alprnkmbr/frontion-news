#!/usr/bin/env python3
"""
linkedin_post.py — Generate and send LinkedIn posts for daily brief.

Usage:
  python3 linkedin_post.py bluf <date>          # Send BLUF post (with image)
  python3 linkedin_post.py section <date> <n>    # Send section n (1-based)
  python3 linkedin_post.py bottomline <date>      # Send Bottom Line post

Each post generates a card image, pushes to GitHub, then sends both
text and image URL to the Make.com webhook.

Environment:
  MAKE_WEBHOOK_URL — Make.com webhook URL
"""

import json
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

SITE_DIR = Path(__file__).parent
SITE_URL = "https://frontion.news"

# Source directories
SOURCES = {
    "brief": SITE_DIR / "briefs",
    "defense": SITE_DIR / "defense",
    "energy": SITE_DIR / "energy",
    "turkey": SITE_DIR / "turkey",
}

# Source-specific base hashtags
SOURCE_HASHTAGS = {
    "brief": ["#Geopolitics", "#Strategy"],
    "defense": ["#DefensePolicy", "#Strategy"],
    "energy": ["#EnergySecurity", "#Strategy"],
    "turkey": ["#Türkiye", "#Strategy"],
}

# Source-specific CTA links
SOURCE_LINKS = {
    "brief": "https://frontion.news/global",
    "defense": "https://frontion.news/defence",
    "energy": "https://frontion.news/energy",
    "turkey": "https://frontion.news/turkey",
}

# Source-specific card filename prefixes
SOURCE_CARD_PREFIX = {
    "brief": "",
    "defense": "defense-",
    "energy": "energy-",
    "turkey": "turkey-",
}

# Current source (default: brief)
CURRENT_SOURCE = "brief"

WEBHOOK_URL = "https://hook.eu1.make.com/w1evieps3ym9ihfkx9qgrwc386saaeis"

# --- LLM-based hashtag selection (primary) ---
# Ollama OpenAI-compatible endpoint for local LLM calls
OLLAMA_API_URL = "http://localhost:11434/v1/chat/completions"
OLLAMA_MODEL = "phi4-mini:latest"  # Fast, small model — good for classification tasks

# Allowed hashtags — LLM can only pick from this list
ALLOWED_HASHTAGS = [
    # Regions
    "#MiddleEast", "#Iran", "#Gaza", "#Lebanon", "#Syria", "#Türkiye",
    "#Ukraine", "#Russia", "#China", "#India", "#Europe", "#EuropeanUnion",
    "#Africa", "#LatinAmerica", "#AsiaPacific", "#Japan", "#Korea", "#Taiwan",
    "#Pakistan", "#NATO",
    # Topics
    "#EnergySecurity", "#NuclearPolicy", "#Sanctions", "#TradeWar", "#GlobalTrade",
    "#CyberSecurity", "#ArtificialIntelligence", "#DefensePolicy", "#Elections",
    "#Democracy", "#PeaceProcess", "#Diplomacy", "#ClimatePolicy",
    "#HumanitarianCrisis", "#EconomicPolicy", "#FederalReserve", "#SupplyChain",
    "#Semiconductors", "#CriticalMinerals", "#OPEC", "#DroneWarfare",
    "#NavalWarfare", "#Intelligence", "#CivilUnrest", "#PoliticalInstability",
    "#Brexit",
    # Source-specific bases (added separately)
    "#Geopolitics", "#Strategy", "#DefensePolicy", "#EnergySecurity",
]

# --- Fallback: keyword-based hashtag selection ---
HASHTAG_TOPICS = {
    # Regions
    "middle east": "#MiddleEast",
    "israel": "#MiddleEast",
    "iran": "#Iran",
    "gaza": "#Gaza",
    "lebanon": "#Lebanon",
    "syria": "#Syria",
    "turkey": "#Türkiye",
    "türkiye": "#Türkiye",
    "ukraine": "#Ukraine",
    "russia": "#Russia",
    "china": "#China",
    "india": "#India",
    "europe": "#Europe",
    "eu ": "#EuropeanUnion",
    "africa": "#Africa",
    "latin america": "#LatinAmerica",
    "colombia": "#LatinAmerica",
    "bolivia": "#LatinAmerica",
    "asia": "#AsiaPacific",
    "japan": "#Japan",
    "korea": "#Korea",
    "taiwan": "#Taiwan",
    # Topics
    "energy": "#EnergySecurity",
    "oil": "#EnergySecurity",
    "gas": "#EnergySecurity",
    "nuclear": "#NuclearPolicy",
    "sanctions": "#Sanctions",
    "trade war": "#TradeWar",
    "tariff": "#TradeWar",
    "trade": "#GlobalTrade",
    "cyber": "#CyberSecurity",
    "ai ": "#ArtificialIntelligence",
    "artificial intelligence": "#ArtificialIntelligence",
    "defense": "#DefensePolicy",
    "military": "#DefensePolicy",
    "election": "#Elections",
    "democracy": "#Democracy",
    "ceasefire": "#PeaceProcess",
    "peace": "#PeaceProcess",
    "diplomacy": "#Diplomacy",
    "treaty": "#Diplomacy",
    "climate": "#ClimatePolicy",
    "refugee": "#HumanitarianCrisis",
    "humanitarian": "#HumanitarianCrisis",
    "economic": "#EconomicPolicy",
    "inflation": "#EconomicPolicy",
    "fed ": "#FederalReserve",
    "interest rate": "#FederalReserve",
    "supply chain": "#SupplyChain",
    "semiconductor": "#Semiconductors",
    "chip": "#Semiconductors",
    "rare earth": "#CriticalMinerals",
    "critical mineral": "#CriticalMinerals",
    "pipeline": "#EnergySecurity",
    "opec": "#OPEC",
    "drone": "#DroneWarfare",
    "submarine": "#NavalWarfare",
    "naval": "#NavalWarfare",
    "spy": "#Intelligence",
    "intelligence": "#Intelligence",
    "espionage": "#Intelligence",
    "protest": "#CivilUnrest",
    "coup": "#PoliticalInstability",
    "revolution": "#PoliticalInstability",
    "khan": "#Pakistan",
    "pakistan": "#Pakistan",
    "exam": "#India",
    "brexit": "#Brexit",
    "nato": "#NATO",
    "switzerland": "#Diplomacy",
    "deal": "#Diplomacy",
    "negotiat": "#Diplomacy",
}

# Base hashtags always included
BASE_HASHTAGS = ["#Geopolitics", "#Strategy"]


def select_hashtags_llm(text, source, max_hashtags=5):
    """Select hashtags using LLM for semantic understanding. Falls back to keyword matching on failure."""
    # Build source label for context
    source_labels = {
        "brief": "Strategic Brief",
        "defense": "Defense Brief",
        "energy": "Energy & Power Brief",
        "turkey": "Türkiye Brief",
    }
    source_label = source_labels.get(source, "Strategic Brief")

    # Source-specific base hashtags always included
    base_tags = SOURCE_HASHTAGS.get(source, ["#Geopolitics", "#Strategy"])

    prompt = (
        f"You are selecting hashtags for a LinkedIn post from Frontion News ({source_label}). "
        f"Given the post content below, select up to {max_hashtags - len(base_tags)} topic hashtags "
        f"that are MOST RELEVANT to the CORE SUBJECT of this specific post.\n\n"
        f"Rules:\n"
        f"1. Only select hashtags for topics that are the MAIN SUBJECT of the post, not merely mentioned in passing.\n"
        f"2. If a country or topic is only mentioned as context (e.g., Japan mentioned as part of a coalition, "
        f"drones mentioned as one small detail), do NOT add a hashtag for it.\n"
        f"3. Prioritize hashtags about WHAT THE POST IS ABOUT, not every entity mentioned.\n"
        f"4. Only use hashtags from the allowed list below.\n"
        f"5. Return ONLY the hashtags separated by spaces, nothing else. No explanation.\n\n"
        f"Allowed hashtags:\n"
        + ", ".join(sorted(set(ALLOWED_HASHTAGS) - set(base_tags))) + "\n\n"
        f"Post content:\n{text[:1500]}"
    )

    try:
        payload = json.dumps({
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 100,
        }).encode("utf-8")

        req = urllib.request.Request(
            OLLAMA_API_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        content = result["choices"][0]["message"]["content"].strip()
        # Parse hashtags from LLM response
        llm_tags = [t.strip() for t in content.split() if t.strip().startswith("#")]
        # Filter to only allowed hashtags
        llm_tags = [t for t in llm_tags if t in ALLOWED_HASHTAGS]
        # Remove base tags (they'll be added separately)
        llm_tags = [t for t in llm_tags if t not in base_tags]
        # Combine base + LLM-selected, deduplicate
        all_tags = base_tags + llm_tags
        seen = set()
        result = []
        for tag in all_tags:
            if tag not in seen:
                seen.add(tag)
                result.append(tag)
        print(f"Hashtags selected by LLM: {result[:max_hashtags]}")
        return result[:max_hashtags]
    except Exception as e:
        print(f"LLM hashtag selection failed ({e}), falling back to keyword matching")
        return select_hashtags_keyword(text, max_hashtags)


def select_hashtags_keyword(text, max_hashtags=5):
    """Select hashtags based on keyword matching (fallback method)."""
    text_lower = text.lower()
    matched = set()
    for keyword, tag in HASHTAG_TOPICS.items():
        if keyword in text_lower:
            matched.add(tag)
    # Combine source-specific base + topic-specific
    base_tags = SOURCE_HASHTAGS.get(CURRENT_SOURCE, ["#Geopolitics", "#Strategy"])
    all_tags = base_tags + sorted(matched)
    # Remove duplicates while preserving order
    seen = set()
    result = []
    for tag in all_tags:
        if tag not in seen:
            seen.add(tag)
            result.append(tag)
    return result[:max_hashtags]


def select_hashtags(text, max_hashtags=5):
    """Select hashtags — LLM first, keyword fallback on failure."""
    return select_hashtags_llm(text, CURRENT_SOURCE, max_hashtags)


def load_brief(date_str):
    """Load brief JSON for a given date from current source."""
    brief_dir = SOURCES[CURRENT_SOURCE]
    brief_path = brief_dir / f"{date_str}.json"
    if not brief_path.exists():
        print(f"Error: Brief not found for {date_str} in {CURRENT_SOURCE}")
        sys.exit(1)
    with open(brief_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_date_display(date_str):
    """Format date like 'June 21, 2026'."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%B %d, %Y")


def git_push_with_retry(retries=3, delay=5):
    """Git push with retry logic for network issues."""
    for attempt in range(1, retries + 1):
        try:
            result = subprocess.run(
                ["git", "push"],
                cwd=SITE_DIR,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                print(f"Git push succeeded (attempt {attempt})")
                return True
            print(f"Git push failed (attempt {attempt}): {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"Git push timed out (attempt {attempt})")
        except Exception as e:
            print(f"Git push error (attempt {attempt}): {e}")
        if attempt < retries:
            time.sleep(delay)
    print("All git push attempts failed")
    return False


def wait_for_url(url, timeout=180, interval=10):
    """Wait for a URL to return HTTP 200."""
    print(f"Waiting for {url} to be accessible...")
    start = time.time()
    attempt = 0
    while time.time() - start < timeout:
        attempt += 1
        try:
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "Frontion-Bot/1.0")
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    elapsed = time.time() - start
                    print(f"URL accessible after {elapsed:.0f}s (attempt {attempt})")
                    return True
        except urllib.error.HTTPError as e:
            print(f"  Attempt {attempt}: HTTP {e.code} {e.reason}")
        except (urllib.error.URLError, OSError) as e:
            print(f"  Attempt {attempt}: {e}")
        time.sleep(interval)
    print(f"URL not accessible after {timeout}s timeout ({attempt} attempts)")
    return False


def generate_card_and_push(date_str, card_type, section_num=None):
    """Generate card image and push to GitHub. Returns the image URL."""
    prefix = SOURCE_CARD_PREFIX.get(CURRENT_SOURCE, "")

    # Generate card — pass source so card generator can use correct brief dir
    args = ["python3", str(SITE_DIR / "linkedin_cards.py"), date_str, card_type, "--source", CURRENT_SOURCE]
    if section_num is not None:
        args.append(str(section_num))
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Card generation failed: {result.stderr}")
        sys.exit(1)
    print(result.stdout)

    # Determine card filename
    cards_dir = SITE_DIR / "linkedin-cards"
    if card_type == "bluf":
        card_file = f"{prefix}bluf-{date_str}.png"
    elif card_type == "section":
        card_file = f"{prefix}section-{section_num}-{date_str}.png"
    elif card_type == "bottomline":
        card_file = f"{prefix}bottomline-{date_str}.png"
    else:
        print(f"Unknown card type: {card_type}")
        sys.exit(1)

    card_path = cards_dir / card_file
    if not card_path.exists():
        print(f"Error: Card file not found at {card_path}")
        sys.exit(1)

    # Git add, commit, push with retry
    subprocess.run(["git", "add", "-f", str(card_path)], cwd=SITE_DIR, check=True)

    # Check if there's anything to commit
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", str(card_path)],
        cwd=SITE_DIR, capture_output=True, text=True
    )
    if status.stdout.strip():
        subprocess.run(
            ["git", "commit", "-m", f"LinkedIn card: {CURRENT_SOURCE} {card_type} {date_str}"],
            cwd=SITE_DIR, check=True
        )
    else:
        print("No changes to commit (card already tracked)")

    if not git_push_with_retry():
        print("FAILED: Could not push card to GitHub. Aborting post.")
        sys.exit(1)

    # Wait for GitHub Pages to serve the file
    image_url = f"{SITE_URL}/linkedin-cards/{card_file}"
    if not wait_for_url(image_url, timeout=60, interval=10):
        print(f"WARNING: Image URL not yet accessible, but proceeding with post anyway: {image_url}")

    return image_url


def send_post(text, image_url=None):
    """Print the LinkedIn post text and image URL (Make.com webhook disabled)."""
    print("=== LINKEDIN POST ===")
    print(text)
    if image_url:
        print(f"Image: {image_url}")
    print("=== END POST ===")
    return True


def send_bluf(date_str):
    """Send BLUF post with image."""
    brief = load_brief(date_str)

    # Generate and push card image
    image_url = generate_card_and_push(date_str, "bluf")

    title = brief.get("title", "")
    subhead = brief.get("subhead", "")

    # Select hashtags based on title + subhead content
    content_text = f"{title} {subhead}"
    hashtags = select_hashtags(content_text, max_hashtags=5)
    hashtag_str = " ".join(hashtags)

    link = SOURCE_LINKS.get(CURRENT_SOURCE, "https://frontion.news")
    text = f"◆ {title}\n\n{subhead}\n\n{hashtag_str}\n\nRead the full analysis at {link}"

    if not send_post(text, image_url=image_url):
        print("FAILED: Could not send BLUF post to Make.com")
        sys.exit(1)


def send_section(date_str, section_num):
    """Send a section post with image (1-based)."""
    brief = load_brief(date_str)
    sections = brief.get("sections", [])

    if section_num < 1 or section_num > len(sections):
        print(f"Error: Section {section_num} not found (brief has {len(sections)} sections)")
        sys.exit(1)

    section = sections[section_num - 1]
    heading = section.get("heading", "")
    body = section.get("body", "")
    why = section.get("whyItMatters", "")

    # Strip HTML tags from body
    if body:
        body = re.sub(r"<[^>]+>", "", body).strip()

    # Select hashtags based on section heading + body + why
    content_text = f"{heading} {body} {why}"
    hashtags = select_hashtags(content_text, max_hashtags=5)
    hashtag_str = " ".join(hashtags)

    text = f"► {heading}\n\n{body}"
    if why:
        text += f"\n\nWhy it matters: {why}"
    text += f"\n\n{hashtag_str}"

    # Generate and push card image
    image_url = generate_card_and_push(date_str, "section", section_num)

    if not send_post(text, image_url=image_url):
        print(f"FAILED: Could not send Section {section_num} post to Make.com")
        sys.exit(1)


def send_bottomline(date_str):
    """Send Bottom Line post with image."""
    brief = load_brief(date_str)
    bottom_line = brief.get("bottomLine", "")

    if not bottom_line:
        print("Error: No bottom line found")
        sys.exit(1)

    # Select hashtags based on bottom line content
    hashtags = select_hashtags(bottom_line, max_hashtags=4)
    hashtag_str = " ".join(hashtags)

    link = SOURCE_LINKS.get(CURRENT_SOURCE, "https://frontion.news")
    text = f"■ The Bottom Line\n\n{bottom_line}\n\n{hashtag_str}\n\nRead the full analysis at {link}"

    # Generate and push card image
    image_url = generate_card_and_push(date_str, "bottomline")

    if not send_post(text, image_url=image_url):
        print("FAILED: Could not send Bottom Line post to Make.com")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 linkedin_post.py <bluf|section|bottomline> <date> [section_num] [--source brief|defense|energy|turkey]")
        sys.exit(1)

    command = sys.argv[1]
    date_str = sys.argv[2]

    # Parse --source flag
    source = "brief"
    remaining = []
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == "--source" and i + 1 < len(sys.argv):
            source = sys.argv[i + 1]
            i += 2
        else:
            remaining.append(sys.argv[i])
            i += 1

    if source not in SOURCES:
        print(f"Unknown source: {source}. Valid: {', '.join(SOURCES.keys())}")
        sys.exit(1)

    CURRENT_SOURCE = source

    if command == "bluf":
        send_bluf(date_str)
    elif command == "section":
        if not remaining:
            print("Usage: python3 linkedin_post.py section <date> <section_num> [--source ...]")
            sys.exit(1)
        send_section(date_str, int(remaining[0]))
    elif command == "bottomline":
        send_bottomline(date_str)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)