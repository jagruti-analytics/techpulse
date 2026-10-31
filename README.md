# TechPulse — AI, Analytics & IT Intelligence Hub

A GitHub Pages-ready, responsive website with searchable technology updates, category filters, time filters, technology watchlists, and links to the original publishers.

## Deploy to GitHub Pages

1. Create a **public GitHub repository**, e.g. `techpulse`.
2. Upload **all files and folders from this package** to the repository root. Preserve `.github/workflows/update-feeds.yml` and `data/articles.json`.
3. Open **Settings → Actions → General → Workflow permissions** and choose **Read and write permissions** (if available), then save. Repository or organizational policies may affect these settings.
4. Go to **Actions → Refresh tech news → Run workflow**. The first run populates `data/articles.json`. The script does **not** insert fabricated headlines if every feed fails.
5. Open **Settings → Pages**, select **Deploy from a branch**, then choose branch `main` and folder `/ (root)`; click Save. Your site will be available at `https://YOUR-USERNAME.github.io/techpulse/` once deployed.
6. The update workflow is scheduled every four hours (UTC). GitHub may delay or skip scheduled runs during high load. Scheduled workflows on public repositories can be disabled after extended inactivity.

## How it works

- `index.html`, `style.css`, `app.js`: the entire static interface; no server and no API keys needed.
- `fetch_feeds.py`: RSS/Atom reader using only Python's standard library, retrieving headlines and short excerpts from curated sources.
- `data/articles.json`: most recent successfully collected news items. Starts empty until the first run.
- `.github/workflows/update-feeds.yml`: runs the reader every four hours, commits updated data to `main`, and thereby refreshes the GitHub Pages site.

Stories always link back to publishers. Not every RSS feed will be available all the time; blocked or invalid feeds are skipped. To customize feed sources, edit the `FEEDS` list in `fetch_feeds.py`. To edit source-directory links, edit the `sources` array in `app.js`.

## Test locally

```bash
python fetch_feeds.py
python -m http.server 8000
```

Visit `http://localhost:8000`. Running the HTML via `file://` is not recommended because browsers restrict JSON `fetch()` in that mode.

## Notes

This is an **automatically updated news feed**, not a scientific ranking of the most popular technologies. Labels follow the source feed category; some articles may be broad. GitHub Pages is a static site host, so updates appear after the scheduled workflow fetches data and Pages redeploys. RSS headlines and snippets remain the property of their publishers.
