import json
import os
import re
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
STATE_PATH = BASE_DIR / "state.json"

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; WebsiteMonitorBot/1.0; +https://github.com/)"
}
REQUEST_TIMEOUT = 20

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def load_json(path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize_text(text):
    return re.sub(r"\s+", " ", text).strip()


def extract_relevant_blocks(html, keywords):
    """
    Scans the page for text blocks (list items, table rows, links,
    paragraphs, divs) that mention any of the given keywords.
    Returns a sorted, deduplicated list of matched text snippets.
    """
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    candidate_tags = soup.find_all(["li", "tr", "a", "p", "div", "span", "h1", "h2", "h3", "h4"])

    keyword_pattern = re.compile(
        "|".join(re.escape(k) for k in keywords), re.IGNORECASE
    )

    matched = set()
    for tag in candidate_tags:
        text = normalize_text(tag.get_text(" "))
        if not text or len(text) < 8 or len(text) > 300:
            continue
        if keyword_pattern.search(text):
            matched.add(text)

    return sorted(matched)


def fetch_site(url):
    resp = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def send_email(receivers, subject, body):
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        print("Missing EMAIL_ADDRESS or EMAIL_APP_PASSWORD env vars, skipping send.")
        return

    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(receivers)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, receivers, msg.as_string())

    print(f"Email sent to {receivers}")


def build_summary(site_name, url, new_items):
    lines = [
        f"Update detected on: {site_name}",
        f"URL: {url}",
        "",
        "New or changed items found:",
        "",
    ]
    for item in new_items[:25]:
        lines.append(f"- {item}")
    if len(new_items) > 25:
        lines.append(f"...and {len(new_items) - 25} more.")
    lines.append("")
    lines.append("This is an automated check, run hourly.")
    return "\n".join(lines)


def main():
    config = load_json(CONFIG_PATH, {"keywords": [], "sites": []})
    state = load_json(STATE_PATH, {})

    keywords = config.get("keywords", [])
    sites = config.get("sites", [])

    if not sites:
        print("No sites configured in config.json. Nothing to do.")
        return

    any_error = False

    for site in sites:
        name = site.get("name", site["url"])
        url = site["url"]
        receivers = site.get("receivers", [])

        print(f"Checking: {name} ({url})")

        try:
            html = fetch_site(url)
        except Exception as e:
            print(f"  Failed to fetch: {e}")
            any_error = True
            continue

        current_items = extract_relevant_blocks(html, keywords)
        previous_items = set(state.get(url, {}).get("items", []))
        current_set = set(current_items)

        new_items = sorted(current_set - previous_items)
        is_first_run = url not in state

        state[url] = {"items": current_items}

        if is_first_run:
            print(f"  First run for this site, baseline saved ({len(current_items)} items).")
            continue

        if new_items:
            print(f"  {len(new_items)} new item(s) found.")
            if receivers:
                subject = f"Update on {name}"
                body = build_summary(name, url, new_items)
                try:
                    send_email(receivers, subject, body)
                except Exception as e:
                    print(f"  Failed to send email: {e}")
                    any_error = True
        else:
            print("  No changes.")

    save_json(STATE_PATH, state)

    if any_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
