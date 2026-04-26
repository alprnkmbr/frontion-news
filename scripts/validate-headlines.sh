#!/bin/bash
# validate-headlines.sh — Check, repair, and merge headlines.json
# Runs every 5 min via LaunchAgent. If JSON is broken, attempts repair and pushes fix.
# Also runs merge-headlines.py to cluster duplicate stories.

HEADLINES="/Users/claudius/clawd/frontion-site/headlines.json"
SITE_DIR="/Users/claudius/clawd/frontion-site"
MERGE_SCRIPT="/Users/claudius/clawd/frontion-site/scripts/merge-headlines.py"
LOG="/tmp/headlines-validator.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') — Running validator" >> "$LOG"

# Check if file exists
if [ ! -f "$HEADLINES" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') — CRITICAL: headlines.json missing!" >> "$LOG"
    # Create minimal valid file
    echo '{"lastUpdated":"","headlines":[]}' > "$HEADLINES"
    cd "$SITE_DIR" && git add headlines.json && git commit -m "validator: recreate missing headlines.json" && git push >> "$LOG" 2>&1
    exit 0
fi

# Check if JSON is valid
NEEDS_PUSH=false

if python3 -c "import json; json.load(open('$HEADLINES'))" 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') — JSON valid" >> "$LOG"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') — JSON BROKEN, attempting repair" >> "$LOG"

    # Attempt repair using Python
    python3 << 'PYEOF' >> "$LOG" 2>&1
import json, re, sys

path = "/Users/claudius/clawd/frontion-site/headlines.json"

with open(path) as f:
    content = f.read()

# Strategy 1: Fix common malformations
fixed = content
fixed = re.sub(r'"\s*\n\s*":\}\]', '"\n    }]', fixed)
fixed = re.sub(r'":\}\s*\n\s*\{', '",\n    {', fixed)
fixed = re.sub(r',\s*\]', ']', fixed)
fixed = re.sub(r',\s*\}', '}', fixed)

try:
    data = json.loads(fixed)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"REPAIRED (strategy 1): {len(data.get('headlines',[]))} headlines recovered")
    sys.exit(0)
except json.JSONDecodeError:
    pass

# Strategy 2: Extract valid headline objects using regex
pattern = r'\{\s*"headline"\s*:.*?"timestamp"\s*:.*?"\s*\}'
matches = re.findall(pattern, content, re.DOTALL)
recovered = []
for m in matches:
    try:
        obj = json.loads(m)
        if 'headline' in obj and 'url' in obj:
            recovered.append(obj)
    except:
        pass

if recovered:
    data = {"lastUpdated": "", "headlines": recovered}
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"REPAIRED (strategy 2): {len(recovered)} headlines recovered via regex extraction")
    sys.exit(0)
else:
    data = {"lastUpdated": "", "headlines": []}
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("REPAIRED (strategy 3): No headlines recoverable, reset to empty")
    sys.exit(0)
PYEOF

    NEEDS_PUSH=true
fi

# Run headline merge/dedup
echo "$(date '+%Y-%m-%d %H:%M:%S') — Running merge" >> "$LOG"
MERGE_OUTPUT=$(python3 "$MERGE_SCRIPT" 2>&1)
MERGE_EXIT=$?
echo "$MERGE_OUTPUT" >> "$LOG"

if [ $MERGE_EXIT -eq 0 ]; then
    # Check if merge changed anything (if it found multi-source stories, it modified the file)
    if echo "$MERGE_OUTPUT" | grep -q "Multi-source stories"; then
        NEEDS_PUSH=true
    fi
fi

# Push if needed
if [ "$NEEDS_PUSH" = true ]; then
    cd "$SITE_DIR" && git add headlines.json && git commit -m "validator: repair + merge headlines" && git push >> "$LOG" 2>&1
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Changes pushed" >> "$LOG"
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') — Done" >> "$LOG"