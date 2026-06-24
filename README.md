# YouTube Playlist Liker 🚀

A small Python utility that likes every video in a YouTube playlist using OAuth 2.0.
(Created because I wanted to like all songs of a playlist to make them favourable in yt music algorithm. Creatd using AI)

---

## Contents

- `like_playlist.py` — script that finds videos in a playlist and likes them
- `client_secrets.json` — (you provide) OAuth 2.0 client credentials
- `token.json` — generated after first run (stores OAuth tokens)

---

## Requirements

- Python 3.8+
- Google Cloud project with **YouTube Data API v3** enabled
- OAuth 2.0 Client ID (Application type: Desktop)

Python packages:

```
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

---

## Setup 🔧

1. Go to Google Cloud Console → APIs & Services → Library → enable **YouTube Data API v3**.
2. Create OAuth 2.0 credentials (Credentials → Create → OAuth client ID → Desktop app).
3. Download the JSON and save it as `client_secrets.json` in this project folder (or pass `--credentials`).

---

## Usage

Basic (interactive):

```
python like_playlist.py "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

Options:

- `--dry-run` — list videos and do not call the API to rate
- `--delay N` — seconds to wait between requests (default: `1.0`)
- `--credentials FILE` — path to OAuth client secrets JSON (default: `client_secrets.json`)
- `--token FILE` — path to store OAuth token (default: `token.json`)
- `--yes` — skip confirmation prompt

Examples:

```
# preview only
python like_playlist.py PLxxxxx --dry-run

# actually like videos (2s delay)
python like_playlist.py PLxxxxx --delay 2 --yes
```

---

## Behavior & limitations ⚠️

- The script acts on the **authenticated Google account** (likes will appear on that account).
- Private playlists or videos you don't have permission to view will not be accessible.
- Rate limits/quota: add `--delay` or pause between runs to avoid hitting API quota.

---

## Troubleshooting

- Missing `client_secrets.json`: create OAuth credentials in Google Cloud and save the file here.
- If you need to re-authenticate, delete `token.json` and re-run the script.
- API errors (403 / 429): increase `--delay`, wait, or check your Google Cloud quota.

---

## Security & privacy

- Do not commit `client_secrets.json` or `token.json` to source control. Add them to `.gitignore`.
- You can revoke the script's access at Google Account → Security → Third-party apps with account access.

---

## Contributing / Next steps

- Add tests, logging, or a GUI wrapper.
- Optionally support CSV import of playlist IDs.

---
