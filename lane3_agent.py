#!/usr/bin/env python3
"""
DangerSky Collectibles - LANE 3 AGENT (Niche Placement Outreach)
----------------------------------------------------------------
What it does, in plain English:
  1. Loads your brand brief (dangersky_brand_brief.md) -- the "brain."
  2. Picks a fandom for the day (rotates: Pokemon, Star Wars, retro/gaming,
     general nostalgia) and uses WEB SEARCH to hunt down small fan sites,
     fan-fiction pages, fan-comic sites, hobby blogs, and forums that match.
  3. For each good prospect it drafts a PACKAGE: the site, why it's a fit,
     who/where to contact, and a warm, personal pitch email you can tweak.
  4. Emails the whole batch to YOU.

  >>> YOU send every email yourself, by hand, from your own personal email. <<<
  This agent NEVER sends outreach. It never touches your website or its email.
  You're the closer -- it just finds the doors and hands you the opening line.

It only proposes FANDOM / HOBBY sites. It skips anything built around a
political or social cause. You approve every single site before any contact.

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

# How many web searches the agent may run per batch (controls cost). 5 is plenty.
MAX_SEARCHES = 5

# The fandoms it rotates through, one per run. Edit this list anytime.
FANDOMS = [
    "Pokemon",
    "Star Wars",
    "retro and classic video games",
    "90s nostalgia and cartoons",
    "general video game fandom",
]
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


def pick_fandom():
    """Rotate fandom by day so each run targets a different niche.
    Override anytime by setting DANGERSKY_FANDOM (e.g. 'Star Wars')."""
    override = os.environ.get("DANGERSKY_FANDOM")
    if override:
        return override
    day_index = datetime.date.today().toordinal()
    return FANDOMS[day_index % len(FANDOMS)]


def build_task(fandom):
    return (
        "You are operating right now as the LANE 3 -- Niche Placement Outreach Agent "
        "for DangerSky Collectibles. Follow PART A (the core) and the LANE 3 MODULE of "
        "the brand brief above.\n\n"
        "TODAY'S FANDOM TARGET: %s\n\n"
        "Use web search to find 3-5 SMALL, real, currently-active fan sites, fan-fiction "
        "pages, fan-comic sites, hobby blogs, or community forums in this fandom that would "
        "be a good home for a paid placement of DangerSky's matching shirts. Favor small/"
        "independent sites (the kind that would actually welcome a paid placement), not giant "
        "corporate ones. SKIP anything organized around a political or social cause -- fandom "
        "and hobby only.\n\n"
        "For EACH prospect, give Justin a clean package with these labeled parts:\n"
        "  - SITE: name + URL\n"
        "  - WHY IT FITS: the fandom + rough sense of the audience\n"
        "  - CONTACT: the best contact path you can find (contact page, owner/admin, email, "
        "or 'check site for contact form')\n"
        "  - DRAFT EMAIL: a short, warm, genuinely personal pitch Justin can tweak and send "
        "from his own email in under a minute. Lead with real appreciation for their site, "
        "then a light, specific pitch -- which DangerSky designs fit their audience, a link to "
        "dangerskycollectibles.com, and an open question about whether they'd consider a paid "
        "placement and what it would run. It must read like a real person, never a templated "
        "blast.\n\n"
        "End with a short note: 'VERIFY BEFORE SENDING -- confirm each site is real, active, "
        "and a fit before you reach out.' Remember: you draft only. Justin sends every email "
        "himself, by hand. You never send anything." % fandom
    )


def call_claude(brief, task):
    payload = {
        "model": MODEL,
        "max_tokens": 4000,
        "system": brief,
        "messages": [{"role": "user", "content": task}],
        "tools": [
            {"type": "web_search_20250305", "name": "web_search", "max_uses": MAX_SEARCHES}
        ],
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

    # Stitch together the text blocks (search results come back interleaved)
    parts = [b.get("text", "") for b in body.get("content", []) if b.get("type") == "text"]
    return "\n".join(p for p in parts if p).strip()


def send_email(subject, body_text):
    safe = body_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = (
        "<div style='font-family:sans-serif;white-space:pre-wrap;"
        "font-size:15px;line-height:1.5'>" + safe + "</div>"
    )
    payload = {
        "from": "DangerSky Lane 3 Agent <%s>" % FROM_EMAIL,
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
    fandom = pick_fandom()
    print("[%s] Lane 3 agent starting -- fandom: %s" % (today, fandom))

    brief = load_brief()
    packages = call_claude(brief, build_task(fandom))

    backup = os.path.join(SCRIPT_DIR, "lane3_prospects_%s.txt" % today)
    with open(backup, "w", encoding="utf-8") as f:
        f.write(packages)
    print("Saved backup to", backup)

    send_email("DangerSky outreach prospects (%s) -- %s" % (fandom, today), packages)
    print("Done.")


if __name__ == "__main__":
    main()
