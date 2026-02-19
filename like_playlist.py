#!/usr/bin/env python3
"""
like_playlist.py — like every video in a YouTube playlist using OAuth 2.0

Setup:
 1. Enable **YouTube Data API v3** in Google Cloud Console.
 2. Create an OAuth 2.0 Client ID (Application type: Desktop) and download the JSON.
    Save it as `client_secrets.json` next to this script (or pass --credentials).
 3. Install dependencies:
    pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

Usage:
  python like_playlist.py PLAYLIST_URL_OR_ID

Options:
  --dry-run         Show videos that would be liked (no API calls to rate).
  --delay N         Seconds to wait between likes (default 1).
  --credentials FILE  Path to client_secrets.json (default: client_secrets.json)
  --token FILE        Path to token file to save OAuth tokens (default: token.json)
  --yes             Skip confirmation prompt.

Important:
 - You CANNOT use a Google "app password" for the YouTube Data API. Use OAuth 2.0.
 - This script acts on the authenticated Google account.
"""

import argparse
import os
import re
import time
from urllib.parse import urlparse, parse_qs

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# scope that allows rating videos
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


def extract_playlist_id(url_or_id: str) -> str:
    """Return the playlist ID from a playlist URL or assume input is an ID."""
    if not url_or_id:
        raise ValueError("Empty playlist id/url")
    parsed = urlparse(url_or_id)
    if parsed.scheme in ("http", "https"):
        qs = parse_qs(parsed.query)
        if "list" in qs:
            return qs["list"][0]
        # sometimes a URL may contain the id in the path (rare for playlists)
    # if looks like a playlist id (common prefixes: PL, UU, FL, OL, RD)
    if re.match(r'^(PL|UU|FL|OL|RD)[A-Za-z0-9_-]+$', url_or_id):
        return url_or_id
    # fallback: return as-is - API will error if invalid
    return url_or_id


def get_authenticated_service(client_secrets_file: str, token_file: str):
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # persist credentials
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def get_video_ids_from_playlist(youtube, playlist_id: str):
    ids = []
    request = youtube.playlistItems().list(part="contentDetails", playlistId=playlist_id, maxResults=50)
    while request:
        resp = request.execute()
        for item in resp.get("items", []):
            vid = item["contentDetails"].get("videoId")
            if vid:
                ids.append(vid)
        request = youtube.playlistItems().list_next(request, resp)
    return ids


def like_video(youtube, video_id: str, max_retries: int = 4) -> bool:
    """Call the API to set rating to 'like'. Returns True on success."""
    for attempt in range(1, max_retries + 1):
        try:
            # videos().rate returns an empty response on success
            youtube.videos().rate(id=video_id, rating="like").execute()
            return True
        except HttpError as e:
            status = getattr(e, 'status_code', None) or (getattr(e, 'resp', None) and e.resp.status)
            if status and int(status) in (403, 429, 500, 503) and attempt < max_retries:
                sleep = 2 ** attempt
                time.sleep(sleep)
                continue
            print(f"Failed to like {video_id}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error liking {video_id}: {e}")
            return False
    return False


def main():
    p = argparse.ArgumentParser(description="Like every video in a YouTube playlist (using OAuth 2.0)")
    p.add_argument("playlist", help="Playlist URL or playlist ID")
    p.add_argument("--dry-run", action="store_true", help="Don't actually like videos; just list them")
    p.add_argument("--delay", type=float, default=1.0, help="Seconds to wait between likes (default 1)")
    p.add_argument("--credentials", default="client_secrets.json", help="Path to OAuth client secrets JSON")
    p.add_argument("--token", default="token.json", help="Path to store OAuth token JSON")
    p.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = p.parse_args()

    playlist_id = extract_playlist_id(args.playlist)
    print(f"Using playlist id: {playlist_id}")

    if args.dry_run:
        print("DRY RUN: will not call YouTube API to rate videos.")

    if not args.dry_run:
        if not os.path.exists(args.credentials):
            print(f"Missing OAuth client secrets: {args.credentials}\nFollow README steps to create it in Google Cloud Console.")
            return
        youtube = get_authenticated_service(args.credentials, args.token)
    else:
        youtube = None

    # gather video IDs
    try:
        video_ids = []
        if youtube:
            video_ids = get_video_ids_from_playlist(youtube, playlist_id)
        else:
            # dry-run: we can still try to parse a public playlist via API-less approach? skip.
            print("For dry-run with a playlist URL you still need to provide a real playlist ID or run without --dry-run to fetch items.")
            return

    except HttpError as e:
        print(f"API error while fetching playlist items: {e}")
        return

    if not video_ids:
        print("No videos found in the playlist (it may be private or empty). Exiting.")
        return

    print(f"Found {len(video_ids)} videos in playlist.")
    if not args.yes:
        ans = input("Proceed to like these videos on the authenticated account? (y/N): ").strip().lower()
        if ans != "y":
            print("Aborted by user.")
            return

    succeeded = 0
    failed = 0
    for i, vid in enumerate(video_ids, start=1):
        print(f"[{i}/{len(video_ids)}] Liking {vid}...", end=" ")
        if args.dry_run:
            print("(dry-run)")
            continue
        ok = like_video(youtube, vid)
        if ok:
            print("OK")
            succeeded += 1
        else:
            print("FAIL")
            failed += 1
        time.sleep(max(0, args.delay))

    print("\nSummary:")
    print(f"  Attempted: {len(video_ids)}")
    print(f"  Succeeded: {succeeded}")
    print(f"  Failed:    {failed}")


if __name__ == "__main__":
    main()
