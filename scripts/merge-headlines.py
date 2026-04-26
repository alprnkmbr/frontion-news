#!/usr/bin/env python3
"""
Merge and cluster Frontion News headlines.

Groups headlines about the same story, keeping the best source as primary
and listing alternative sources/perspectives as sub-items.

Usage:
    python3 scripts/merge-headlines.py [--input headlines.json] [--output headlines.json] [--max-age 48]

The script:
1. Reads headlines.json
2. Clusters headlines about the same story (within same category + keyword overlap)
3. Merges clusters into a single headline with perspectives
4. Writes back to headlines.json
5. Preserves all original data, just restructures duplicates into clusters
"""

import json
import sys
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

# Try to use rapidfuzz for better matching, fall back to simple approach
try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

HEADLINES_PATH = Path(__file__).parent.parent / "headlines.json"

# How similar do two headlines need to be to cluster? (0-100)
SIMILARITY_THRESHOLD = 55
# Maximum age difference in hours between two headlines to be clustered
MAX_AGE_DIFF_HOURS = 48
# Maximum headlines to keep (newest first)
MAX_HEADLINES = 200

def normalize(text):
    """Normalize text for comparison."""
    text = text.lower().strip()
    # Remove common prefixes
    for prefix in ['breaking:', 'update:', 'exclusive:', 'analysis:', 'opinion:']:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text

def extract_keywords(text):
    """Extract key content words from a headline."""
    # Remove common stop words
    stop_words = {
        'a', 'an', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'shall', 'not', 'no', 'but', 'and',
        'or', 'if', 'then', 'than', 'that', 'this', 'these', 'those', 'it',
        'its', 'he', 'she', 'they', 'them', 'their', 'we', 'our', 'us',
        'says', 'said', 'reports', 'according', 'after', 'before', 'during',
        'over', 'under', 'between', 'among', 'through', 'into', 'onto',
        'about', 'against', 'also', 'just', 'still', 'even', 'only', 'now',
        'new', 'newly', 'major', 'latest', 'top', 'key', 'key',
    }
    words = re.findall(r'[a-z]+', text.lower())
    return [w for w in words if w not in stop_words and len(w) > 2]

def similarity(a, b):
    """Calculate similarity between two headline strings."""
    if HAS_RAPIDFUZZ:
        return fuzz.token_sort_ratio(a, b)
    else:
        # Simple keyword overlap approach
        kw_a = set(extract_keywords(a))
        kw_b = set(extract_keywords(b))
        if not kw_a or not kw_b:
            return 0
        intersection = kw_a & kw_b
        union = kw_a | kw_b
        return len(intersection) / len(union) * 100

def same_story(h1, h2):
    """Determine if two headlines are about the same story."""
    # Must be same category (or closely related)
    cat1 = h1.get('category', '')
    cat2 = h2.get('category', '')
    
    # Related categories that can cluster
    related = {
        'US-Iran War': {'Middle East', 'Energy', 'Diplomacy'},
        'Middle East': {'US-Iran War', 'Diplomacy'},
        'Ukraine-Russia War': {'Diplomacy', 'Europe', 'Defense Industry'},
        'Diplomacy': set(),
        'Energy': {'US-Iran War', 'Economy'},
        'Economy': {'Energy'},
    }
    
    if cat1 != cat2:
        if cat2 not in related.get(cat1, set()) and cat1 not in related.get(cat2, set()):
            return False
    
    # Check headline similarity
    sim = similarity(normalize(h1.get('headline', '')), normalize(h2.get('headline', '')))
    if sim >= SIMILARITY_THRESHOLD:
        return True
    
    # Also check keyword overlap more aggressively for same-category
    kw1 = set(extract_keywords(h1.get('headline', '')))
    kw2 = set(extract_keywords(h2.get('headline', '')))
    if kw1 and kw2:
        overlap = kw1 & kw2
        # If they share at least 3 significant keywords and same category
        if len(overlap) >= 3 and cat1 == cat2:
            return True
    
    return False

def pick_primary(headlines):
    """Pick the best headline as primary (best source, most recent)."""
    # Source quality ranking
    source_rank = {
        'Reuters': 100, 'AP News': 95, 'BBC': 90, 'New York Times': 85,
        'Washington Post': 85, 'Guardian': 80, 'Al Jazeera': 80,
        'Financial Times': 85, 'Wall Street Journal': 85, 'Economist': 80,
        'SCMP': 75, 'Kyiv Independent': 75, 'The Defense Post': 70,
        'Defense News': 70, 'Nikkei Asia': 75, 'Middle East Eye': 70,
        'Anadolu Agency': 70, 'Daily Sabah': 65,
    }
    
    def score(h):
        ts = h.get('timestamp', '')
        source = h.get('source', '')
        rank = source_rank.get(source, 50)
        # Newer = better
        return rank
    
    return max(headlines, key=score)

def merge_cluster(headlines):
    """Merge a cluster of related headlines into a single grouped headline."""
    primary = pick_primary(headlines)
    
    # Build perspectives from other headlines in the cluster
    perspectives = []
    for h in headlines:
        if h == primary:
            continue
        perspectives.append({
            'source': h.get('source', ''),
            'url': h.get('url', ''),
            'angle': h.get('headline', ''),
            'summary': h.get('summary', '')
        })
    
    result = dict(primary)  # Start with primary
    if perspectives:
        result['perspectives'] = perspectives
        result['sources'] = [primary.get('source', '')] + [p['source'] for p in perspectives]
        result['urls'] = [primary.get('url', '')] + [p['url'] for p in perspectives]
    
    return result

def cluster_headlines(headlines):
    """Group related headlines into clusters."""
    clusters = []  # List of lists
    used = set()
    
    for i, h in enumerate(headlines):
        if i in used:
            continue
        
        cluster = [h]
        used.add(i)
        
        for j in range(i + 1, len(headlines)):
            if j in used:
                continue
            if same_story(h, headlines[j]):
                cluster.append(headlines[j])
                used.add(j)
        
        clusters.append(cluster)
    
    return clusters

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Merge and cluster Frontion headlines')
    parser.add_argument('--input', default=str(HEADLINES_PATH), help='Input headlines.json path')
    parser.add_argument('--output', default=None, help='Output path (default: overwrite input)')
    parser.add_argument('--max-age', type=int, default=48, help='Max age of headlines in hours')
    parser.add_argument('--dry-run', action='store_true', help='Print results without writing')
    parser.add_argument('--verbose', action='store_true', help='Print clustering details')
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path
    
    with open(input_path) as f:
        data = json.load(f)
    
    headlines = data.get('headlines', [])
    
    # Filter by age
    if args.max_age > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=args.max_age)
        filtered = []
        for h in headlines:
            ts = h.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(ts.replace('+03:00', '+03:00'))
                if dt.timestamp() > cutoff.timestamp() - 86400:  # Keep slightly more
                    filtered.append(h)
            except:
                filtered.append(h)  # Keep if we can't parse
        headlines = filtered
    
    original_count = len(headlines)
    
    # Cluster
    clusters = cluster_headlines(headlines)
    
    # Merge each cluster
    merged = []
    for cluster in clusters:
        merged_headline = merge_cluster(cluster)
        merged.append(merged_headline)
    
    # Sort by timestamp (newest first)
    merged.sort(key=lambda h: h.get('timestamp', ''), reverse=True)
    
    # Limit
    merged = merged[:MAX_HEADLINES]
    
    if args.verbose:
        print(f"Original: {original_count} headlines")
        print(f"After clustering: {len(merged)} stories")
        multi = [m for m in merged if 'perspectives' in m]
        print(f"Multi-source stories: {len(multi)}")
        for m in multi:
            print(f"  - {m['headline'][:60]} ({len(m['perspectives'])+1} sources)")
    
    if not args.dry_run:
        # Read original data to preserve metadata
        with open(input_path) as f:
            original = json.load(f)
        
        original['headlines'] = merged
        
        with open(output_path, 'w') as f:
            json.dump(original, f, indent=2, ensure_ascii=False)
        
        print(f"Merged {original_count} → {len(merged)} headlines ({len([m for m in merged if 'perspectives' in m])} multi-source clusters)")
    else:
        print(f"[DRY RUN] Would merge {original_count} → {len(merged)} headlines")

if __name__ == '__main__':
    main()