#!/usr/bin/env python3
"""
linkedin_schedule.py — Create OpenClaw cron jobs to auto-post LinkedIn cards.

Called automatically after brief generation. Reads the brief, counts sections,
and creates cron jobs with 30-min intervals starting from a specified time.

Usage:
  python3 linkedin_schedule.py <date> [--source brief|defense|energy|turkey] [--start HH:MM] [--delay-minutes N]

If --start is not given, schedules first post N minutes from now (--delay-minutes, default 30).
"""

import json
import sys
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

SITE_DIR = Path(__file__).parent
BRIEF_DIRS = {
    "brief": SITE_DIR / "briefs",
    "defense": SITE_DIR / "defense",
    "energy": SITE_DIR / "energy",
    "turkey": SITE_DIR / "turkey",
}

INTERVAL_MINUTES = 30
TR_TZ_OFFSET = timedelta(hours=3)  # UTC+3 for Turkey


def count_sections(date_str, source="brief"):
    brief_path = BRIEF_DIRS[source] / f"{date_str}.json"
    if not brief_path.exists():
        print(f"Error: Brief not found at {brief_path}")
        sys.exit(1)
    with open(brief_path) as f:
        brief = json.load(f)
    return len(brief.get("sections", []))


def create_cron_job(name, iso_time, command, timeout=300):
    """Create an OpenClaw cron job via the openclaw CLI."""
    # Use openclaw cron add command
    # We'll use the gateway API instead for more control
    import urllib.request
    
    # Build the job payload for OpenClaw cron API
    payload = {
        "name": name,
        "schedule": {
            "kind": "at",
            "at": iso_time
        },
        "sessionTarget": "isolated",
        "payload": {
            "kind": "agentTurn",
            "message": f"Run: {command}",
            "timeoutSeconds": timeout,
            "toolsAllow": ["exec"]
        },
        "delivery": {
            "mode": "none"
        },
        "deleteAfterRun": True,
        "enabled": True
    }
    
    # Write payload to temp file and use openclaw CLI
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(payload, f, indent=2)
        temp_path = f.name
    
    try:
        result = subprocess.run(
            ["openclaw", "cron", "add", "--json", temp_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            # Fallback: use the gateway REST API
            print(f"  CLI failed, using REST API...")
            return create_cron_via_api(payload)
        output = result.stdout.strip()
        print(f"  ✓ Created: {name} at {iso_time}")
        return True
    except FileNotFoundError:
        print(f"  CLI not found, using REST API...")
        return create_cron_via_api(payload)
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


def create_cron_via_api(payload):
    """Fallback: create cron job via gateway REST API."""
    # This is handled by the calling agent (OpenClaw) directly
    # Print the payload so the agent can create it
    print(f"  API fallback needed for: {payload['name']}")
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 linkedin_schedule.py <date> [--source brief|defense|energy|turkey] [--start HH:MM] [--delay-minutes N]")
        sys.exit(1)
    
    date_str = sys.argv[1]
    source = "brief"
    start_time = None
    delay_minutes = 30
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--source" and i + 1 < len(sys.argv):
            source = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--start" and i + 1 < len(sys.argv):
            start_time = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--delay-minutes" and i + 1 < len(sys.argv):
            delay_minutes = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    
    n_sections = count_sections(date_str, source)
    
    # Build post list: BLUF, S1...Sn, BottomLine
    posts = []
    posts.append(("bluf", f"bluf {date_str}"))
    for s in range(1, n_sections + 1):
        posts.append((f"S{s}", f"section {date_str} {s}"))
    posts.append(("bottomline", f"bottomline {date_str}"))
    
    total = len(posts)
    source_flag = f" --source {source}" if source != "brief" else ""
    
    # Calculate start time
    now = datetime.now(timezone.utc)
    if start_time:
        # Parse HH:MM as TR time
        h, m = map(int, start_time.split(":"))
        start_dt = datetime(now.year, now.month, now.day, h, m, 0, tzinfo=timezone(TR_TZ_OFFSET))
        if start_dt < now.astimezone(timezone(TR_TZ_OFFSET)):
            # Start time is in the past, use tomorrow
            start_dt += timedelta(days=1)
        base_dt = start_dt.astimezone(timezone.utc)
    else:
        base_dt = now + timedelta(minutes=delay_minutes)
    
    # Output job specifications as JSON for OpenClaw to pick up
    jobs = []
    for idx, (label, post_type) in enumerate(posts):
        run_dt = base_dt + timedelta(minutes=INTERVAL_MINUTES * idx)
        iso_time = run_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        command = f"python3 /Users/claudius/clawd/frontion-site/linkedin_post.py {post_type}{source_flag}"
        
        if label == "bluf":
            name = f"LinkedIn {source.title()} BLUF — {date_str}"
        elif label == "bottomline":
            name = f"LinkedIn {source.title()} Bottom Line — {date_str}"
        else:
            name = f"LinkedIn {source.title()} {label} — {date_str}"
        
        jobs.append({
            "name": name,
            "at": iso_time,
            "command": command,
            "label": label,
        })
    
    # Print summary
    tr_tz = timezone(TR_TZ_OFFSET)
    print(f"\nLinkedIn Post Schedule for {date_str} ({source}):")
    print(f"{'='*60}")
    for j in jobs:
        local_time = datetime.fromisoformat(j['at'].replace('Z', '+00:00')).astimezone(tr_tz)
        print(f"  {local_time.strftime('%H:%M')} TR — {j['label']}")
    print(f"{'='*60}")
    print(f"Total: {total} posts, {INTERVAL_MINUTES}-min intervals")
    
    # Output as JSON for programmatic use
    output = {"date": date_str, "source": source, "total": total, "interval_minutes": INTERVAL_MINUTES, "jobs": jobs}
    print(f"\n__SCHEDULE_JSON__")
    print(json.dumps(output))


if __name__ == "__main__":
    main()