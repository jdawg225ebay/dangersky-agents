#!/usr/bin/env python3
"""
DangerSky Collectibles - LANE 4 AGENT (Video Studio: TikTok / Reels)
--------------------------------------------------------------------
What it does, in plain English:
  1. Loads your brand brief (dangersky_brand_brief.md) -- the "brain."
  2. Writes a BATCH of 5 complete, Canva-ready video briefs -- hook,
     scene-by-scene shot list, on-screen text, voiceover/caption, music vibe,
     TikTok caption + hashtags, and CTA. Varied formats, not 5 of the same.
  3. Emails the batch to you. You drop your product photos into a Canva
     template, follow the brief, export vertical, and post. Lots of videos,
     barely any work.

  Claude writes the words and the plan. CANVA renders the actual video.

  >>> THE TWO TESTS (hard rules for this lane) <<<
  Every video must be (1) IP-clean -- no franchise material (TikTok bans
  franchise merch) -- and (2) politics-clean -- no politician/party/slogan
  (TikTok bans political merch). Generic patriotic is fine. Franchise +
  named-figure designs do NOT go in TikTok videos; they live on Lanes 2 & 3.

  >>> Quick glance before posting <<< account equity is on the line, so review
  the batch (10 seconds) before you make/post. Nothing auto-posts from here.

  >>> SECURITY: keep your API keys out of GitHub. Same rules as the Lane 2 agent.
  Needs nothing extra installed -- only Python's built-in tools.
"""

import os
import sys
import json
import datetime
import urllib.request
import urllib.error

# =====================================================================
# CONFIG  -- fill these in, OR set them as environment variables on the server
# =====================================================================
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "PASTE_YOUR_ANTHROPIC_KEY_HERE")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "PASTE_YOUR_RESEND_KEY_HERE")
FROM_EMAIL = os.environ.get("DANGERSKY_FROM_EMAIL", "agent@dangerskycollectibles.com")
TO_EMAIL = os.environ.get("DANGERSKY_REVIEW_EMAIL", "PASTE_YOUR_REVIEW_EMAIL_HERE")
MODEL = "claude-sonnet-4-6"

# How many video briefs to produce per run.
VIDEOS_PER_RUN = 5

# Optional theme focus for the day (e.g. "Pokemon-inspired", "retro gaming",
# "generic patriotic"). Leave blank to let the agent mix across the brand.
# Remember: inspired-by only -- never actual franchise material on TikTok.
THEME = os.environ.get("DANGERSKY_VIDEO_THEME", "")
# =====================================================================


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BRIEF_PATH = os.path.join(SCRIPT_DIR, "dangersky_brand_brief.md")


def load_brief():
    try:
        with open(BRIEF_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        sys.exit(
            "ERROR: Could not find the brand brief at %s\n"
            "Put dangersky_brand_brief.md in the SAME folder as this script."
            % BRIEF_PATH
        )


def build_task():
    theme_line = ""
    if THEME:
        theme_line = ("TODAY'S THEME FOCUS: %s (inspired-by only -- never actual "
                      "franchise material).\n\n" % THEME)
    return (
        "You are operating right now as the LANE 4 -- Video Studio Agent for DangerSky "
        "Collectibles. Follow PART A (the core) and the LANE 4 MODULE of the brand brief "
        "above.\n\n"
        + theme_line +
        "Produce %d distinct, Canva-ready video briefs for TikTok/Reels. VARY the formats "
        "(don't repeat the same structure) -- mix product showcase, POV/relatable fan moment, "
        "problem->solution, drop/reveal, before-after styling, top-3 list, behind-the-brand.\n\n"
        "HARD RULE: every video must pass BOTH tests -- IP-clean (no franchise material at all) "
        "and politics-clean (no politician/party/slogan; generic patriotic is OK). If a design "
        "would fail either, don't build a video for it.\n\n"
        "For EACH of the %d briefs, give ALL of these clearly labeled parts:\n"
        "  1. CONCEPT -- format + the design featured (confirm it passes both tests)\n"
        "  2. HOOK (0-2 sec) -- the scroll-stopping opening line/visual (most important part)\n"
        "  3. SCENE-BY-SCENE -- short shot list w/ rough timings, what's on screen, motion/"
        "transitions, built vertical 9:16\n"
        "  4. ON-SCREEN TEXT -- exact overlay text per scene, kept out of the bottom-third / "
        "right-side TikTok UI safe zone\n"
        "  5. VOICEOVER/CAPTION SCRIPT -- exact words if voiceover, else spoken-style caption\n"
        "  6. MUSIC VIBE -- the STYLE/energy of sound to pick in Canva (do NOT name specific "
        "copyrighted tracks)\n"
        "  7. TIKTOK CAPTION + HASHTAGS -- in Justin's voice; tight, relevant fan/hobby tags "
        "(no trademarked-merch tags)\n"
        "  8. CTA -- clear path to dangerskycollectibles.com\n"
        "  9. BUILD STEPS (beginner, click-by-click) -- exact plain instructions a total "
        "beginner can follow to assemble this video, starting from a saved reusable template. "
        "No jargon. Spell out every tap: which photo goes where, what text to paste into which "
        "spot, how long each clip runs, which transition, and how to export a vertical 9:16 MP4 "
        "for TikTok. Justin learns by exact steps, not concepts. Write the steps as 'open your "
        "saved DangerSky template and...' so he never starts from a blank page. (These also "
        "work in CapCut or TikTok's built-in photo/video mode if he prefers something simpler "
        "than Canva.)\n\n"
        "Keep Justin's voice: direct, casual, fan-to-fan, hype but real, never corporate. Make "
        "each brief lean on a REUSABLE Canva template idea so future videos are just 'drop new "
        "photos into the same frame.' If anything needs Justin's judgment, flag it at the end "
        "under 'FLAGGED FOR JUSTIN.'" % (VIDEOS_PER_RUN, VIDEOS_PER_RUN)
    )


def call_claude(brief):
    payload = {
        "model": MODEL,
        "max_tokens": 6000,
        "system": brief,
        "messages": [{"role": "user", "content": build_task()}],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit("ERROR talking to Claude API: %s %s" % (e.code, e.read().decode("utf-8")))
    except Exception as e:
        sys.exit("ERROR talking to Claude API: %s" % e)

    parts = [b.get("text", "") for b in body.get("content", []) if b.get("type") == "text"]
    return "\n".join(parts).strip()


def send_email(subject, body_text):
    safe = body_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = (
        "<div style='font-family:sans-serif;white-space:pre-wrap;"
        "font-size:15px;line-height:1.5'>" + safe + "</div>"
    )
    payload = {
        "from": "DangerSky Video Studio <%s>" % FROM_EMAIL,
        "to": [TO_EMAIL],
        "subject": subject,
        "html": html,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=data,
        headers={
            "Authorization": "Bearer %s" % RESEND_API_KEY,
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp.read()
        print("Email sent to", TO_EMAIL)
    except urllib.error.HTTPError as e:
        print("WARNING: email failed: %s %s" % (e.code, e.read().decode("utf-8")))
    except Exception as e:
        print("WARNING: email failed: %s" % e)


def main():
    today = datetime.date.today().isoformat()
    print("[%s] Lane 4 Video Studio starting..." % today)

    brief = load_brief()
    briefs = call_claude(brief)

    backup = os.path.join(SCRIPT_DIR, "lane4_videos_%s.txt" % today)
    with open(backup, "w", encoding="utf-8") as f:
        f.write(briefs)
    print("Saved backup to", backup)

    send_email("DangerSky video briefs for Canva -- %s" % today, briefs)
    print("Done.")


if __name__ == "__main__":
    main()
