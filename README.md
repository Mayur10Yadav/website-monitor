# Website monitor

Checks a list of websites every hour. If it finds new text mentioning
things like "circular", "notice", "notification", "announcement", or
"advertisement", it emails you a summary. Runs for free on GitHub
Actions — no server needed.

## How it works

- `config.json` — your list of sites, keywords, and who gets emailed for each.
- `monitor.py` — fetches each site, scans for text blocks matching your
  keywords, compares them to the last run, and emails anything new.
- `state.json` — auto-generated, stores what was seen last time. The
  workflow commits this back to the repo after every run so it
  remembers between hours.
- `.github/workflows/monitor.yml` — the schedule. Runs at the top of
  every hour automatically, or anytime from the Actions tab manually.

## Setup (about 10 minutes)

### 1. Create a GitHub repo
Create a new repo (public or private both work) and upload these files,
keeping the folder structure as-is (the `.github/workflows/monitor.yml`
path matters).

### 2. Get a Gmail app password
Regular Gmail passwords won't work for this — you need an "app password":
1. Go to https://myaccount.google.com/security
2. Turn on 2-Step Verification if it isn't already on.
3. Search for "App passwords" in your Google Account settings.
4. Create one (name it anything, e.g. "website monitor"). Copy the
   16-character password shown.

### 3. Add GitHub secrets
In your repo: **Settings → Secrets and variables → Actions → New repository secret**
Add two secrets:
- `EMAIL_ADDRESS` — your Gmail address (the one sending the emails)
- `EMAIL_APP_PASSWORD` — the 16-character app password from step 2

### 4. Edit `config.json`
Add your real sites and keywords:

```json
{
  "keywords": ["circular", "notice", "notification", "advertisement"],
  "sites": [
    {
      "name": "My College Notices",
      "url": "https://mycollege.edu/notices",
      "receivers": ["me@gmail.com"]
    }
  ]
}
```

- `keywords` applies globally to all sites — add or remove words freely.
- Each site can list multiple `receivers`.
- Add as many sites as you like — just add more entries to the array.

### 5. Turn it on
Commit and push your changes. The workflow starts running automatically
every hour. To test it immediately instead of waiting: go to the
**Actions** tab → **Website monitor** → **Run workflow**.

The very first run for each site just saves a baseline (no email sent,
since there's nothing to compare against yet). From the second run
onward, any new matching content triggers an email.

## Notes and limits

- GitHub's free-tier cron schedule can run a few minutes late during
  high-traffic periods — it's "hourly-ish," not to-the-second.
- Some sites block automated requests or require JavaScript to render
  content; if a site never detects changes, that's likely why — let me
  know the URL and I can help adjust the approach for that site.
- Keyword matching is generic on purpose so it works across different
  site layouts. If a specific site needs tighter targeting (e.g. only
  one exact section of the page), share the URL and I can add a
  site-specific rule.
