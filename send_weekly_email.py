#!/usr/bin/env python3
"""
Send Frontion Weekly Brief email via Brevo API.

Reads weekly/YYYY-MM-DD.json, generates HTML email from template,
fetches subscriber list from Brevo, and sends.

Usage:
    python3 send_weekly_email.py YYYY-MM-DD
    python3 send_weekly_email.py          # uses latest from index.json
"""

import json
import sys
import os
import urllib.request
import urllib.error
from datetime import datetime

# --- Config ---
BREVO_API_KEY = os.environ.get('BREVO_API_KEY')
BREVO_LIST_ID = 4
SENDER_EMAIL = 'frontion.net@gmail.com'
SENDER_NAME = 'Frontion News'
SITE_URL = 'https://frontion.news'
WEEKLY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weekly')


def format_date_range(date_str):
    """Convert 2026-06-21 to 'June 15–21, 2026' for the week containing that date."""
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    # Find Monday of that week
    monday = dt - timedelta(days=dt.weekday())
    sunday = monday + timedelta(days=6)
    months = ['January','February','March','April','May','June','July','August','September','October','November','December']
    if monday.month == sunday.month:
        return f"{months[monday.month-1]} {monday.day}–{sunday.day}, {monday.year}"
    else:
        return f"{months[monday.month-1]} {monday.day}–{months[sunday.month-1]} {sunday.day}, {sunday.year}"


def load_weekly_data(date_str=None):
    """Load weekly brief JSON data."""
    if date_str is None:
        # Load latest from index
        index_path = os.path.join(WEEKLY_DIR, 'index.json')
        with open(index_path) as f:
            index = json.load(f)
        date_str = index[0]['date']
    
    json_path = os.path.join(WEEKLY_DIR, f'{date_str}.json')
    with open(json_path) as f:
        return json.load(f)


def generate_html(data):
    """Generate HTML email from weekly brief data, matching the site design."""
    date_str = data['date']
    week_range = data.get('weekRange', '')
    
    # Parse week range for display
    if ' to ' in week_range:
        parts = week_range.split(' to ')
        start = datetime.strptime(parts[0].strip(), '%Y-%m-%d')
        end = datetime.strptime(parts[1].strip(), '%Y-%m-%d')
        months = ['January','February','March','April','May','June','July','August','September','October','November','December']
        if start.month == end.month:
            date_display = f"{months[start.month-1]} {start.day}&ndash;{end.day}, {start.year}"
        else:
            date_display = f"{months[start.month-1]} {start.day}&ndash;{months[end.month-1]} {end.day}, {end.year}"
    else:
        date_display = week_range
    
    sections_html = ""
    for section in data['sections']:
        body = section['body']
        # Remove <p> tags and rewrap for email
        paragraphs = body.replace('</p><p>', '</p>\n<p>').split('\n')
        
        section_html = f"""
    <div style="margin-bottom: 36px;">
      <h2 style="font-family: 'Playfair Display', Georgia, serif; font-size: 19px; font-weight: 700; color: #1a1a1a; margin: 0 0 12px 0; line-height: 1.3;">{section['heading']}</h2>
      <div style="font-family: 'Noto Serif', Georgia, serif; font-size: 15px; line-height: 1.7; color: #333; text-align: justify;">{body}</div>
      <div style="margin-top: 10px; padding: 10px 14px; background: #f7f5f2; border-left: 3px solid #8b7355; font-family: 'Noto Serif', Georgia, serif; font-size: 14px; line-height: 1.6; color: #555; text-align: justify;">
        <strong style="color: #8b7355;">Why it matters:</strong> {section['whyItMatters']}
      </div>
    </div>"""
        sections_html += section_html
    
    html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@400;500;600&family=Noto+Serif:wght@400;700&display=swap" rel="stylesheet"/>
</head>
<body style="margin: 0; padding: 0; background: #f0ede8;"><img width="1" height="1" src="https://frontion.news/pixel.gif" style="mso-hide:all"/>
<div style="max-width: 640px; margin: 0 auto; padding: 40px 24px; background: #ffffff;">

  <div style="text-align: center; padding-bottom: 24px; border-bottom: 2px solid #1a1a1a; margin-bottom: 32px;">
    <a href="{SITE_URL}" style="text-decoration: none; color: #1a1a1a;">
      <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 28px; font-weight: 700; color: #1a1a1a; letter-spacing: 3px; margin-bottom: 4px;">FRONTION</div>
    </a>
    <div style="font-family: 'Inter', Arial, sans-serif; font-size: 11px; font-weight: 600; color: #8b7355; letter-spacing: 4px; text-transform: uppercase;">Weekly Brief</div>
    <div style="font-family: 'Inter', Arial, sans-serif; font-size: 12px; color: #888; margin-top: 8px;">{date_display}</div>
  </div>

  <h1 style="font-family: 'Playfair Display', Georgia, serif; font-size: 26px; font-weight: 700; color: #1a1a1a; line-height: 1.25; margin: 0 0 12px 0;">{data['title']}</h1>
  <p style="font-family: 'Noto Serif', Georgia, serif; font-size: 16px; line-height: 1.65; color: #444; text-align: justify; margin: 0 0 32px 0;">{data['subhead']}</p>

{sections_html}

  <div style="margin-top: 36px; padding: 20px 24px; background: #1a1a1a; color: #f0ede8;">
    <h2 style="font-family: 'Inter', Arial, sans-serif; font-size: 17px; font-weight: 600; color: #f0ede8; margin: 0 0 10px 0;">The Bottom Line</h2>
    <p style="font-family: 'Noto Serif', Georgia, serif; font-size: 15px; line-height: 1.7; color: #d4cfc7; text-align: justify; margin: 0;">{data['bottomLine']}</p>
  </div>

  <div style="margin-top: 28px; padding-top: 20px; border-top: 1px solid #ddd; font-family: 'Inter', Arial, sans-serif; font-size: 11px; color: #999; text-align: center;">
    <a href="{SITE_URL}" style="color: #1a1a1a; text-decoration: none; font-weight: 500;">Frontion News</a> &mdash; Strategic analysis of the events reshaping the world.
  </div>

</div>
</body></html>"""
    
    return html


def get_subscribers():
    """Fetch subscriber list from Brevo."""
    url = f'https://api.brevo.com/v3/contacts/lists/{BREVO_LIST_ID}/contacts?limit=500'
    req = urllib.request.Request(url, headers={'api-key': BREVO_API_KEY})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    
    subscribers = []
    for c in data.get('contacts', []):
        name = (c.get('firstName', '') + ' ' + c.get('lastName', '')).strip()
        subscribers.append({'email': c['email'], 'name': name or 'Subscriber'})
    
    return subscribers


def send_email(html, subject, subscribers):
    """Send email via Brevo transactional API."""
    payload = json.dumps({
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": s['email'], "name": s['name']} for s in subscribers],
        "subject": subject,
        "htmlContent": html
    }).encode('utf-8')
    
    req = urllib.request.Request(
        'https://api.brevo.com/v3/smtp/email',
        data=payload,
        headers={
            'api-key': BREVO_API_KEY,
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            response = json.loads(resp.read().decode())
            print(f"✅ EMAIL SENT to {len(subscribers)} subscribers")
            print(f"   Message ID: {response.get('messageId', 'N/A')}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ ERROR: {e.code}")
        print(f"   {error_body}")
        return False


def main():
    # Load date argument or use latest
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        index_path = os.path.join(WEEKLY_DIR, 'index.json')
        with open(index_path) as f:
            index = json.load(f)
        date_str = index[0]['date']
        print(f"No date specified, using latest: {date_str}")
    
    # Load data
    data = load_weekly_data(date_str)
    print(f"Loaded weekly brief: {data['title']} ({date_str})")
    
    # Generate subject
    week_range = data.get('weekRange', '')
    if ' to ' in week_range:
        parts = week_range.split(' to ')
        start = datetime.strptime(parts[0].strip(), '%Y-%m-%d')
        end = datetime.strptime(parts[1].strip(), '%Y-%m-%d')
        months_short = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        subject = f"Frontion Weekly Brief — {months_short[start.month-1]} {start.day}–{end.day}"
    else:
        subject = f"Frontion Weekly Brief — {date_str}"
    
    # Generate HTML
    html = generate_html(data)
    
    # Get subscribers
    print("Fetching subscribers from Brevo...")
    subscribers = get_subscribers()
    print(f"Found {len(subscribers)} subscribers")
    
    # Send
    print(f"Sending: {subject}")
    success = send_email(html, subject, subscribers)
    
    if success:
        print("Done!")
    else:
        print("Failed!")
        sys.exit(1)


if __name__ == '__main__':
    # Need timedelta for date calculations
    from datetime import timedelta
    main()