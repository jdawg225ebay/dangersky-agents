#!/usr/bin/env python3
"""
DangerSky Collectibles - LANE 2 AGENT (Home Turf / Community + Content)
----------------------------------------------------------------------
What it does, in plain English:
  1. Loads your brand brief (dangersky_brand_brief.md) -- that's the "brain."
  2. Asks Claude to write a batch of READY-TO-REVIEW drafts for your OWN
     channels: community-group posts, your own social posts, and a blog idea.
  3. Emails the whole batch to you so you can read it on your phone, tweak,
     and post it yourself. NOTHING is posted automatically. You are the
     final yes on everything.

This is the SAFE first agent: no ad money, no outreach. Just drafting.

  >>> IMPORTANT SECURITY NOTE <<<
  Your API keys are SECRET, like passwords. Do NOT upload this file to GitHub
  with your keys pasted into it. Best practice (shown in the deploy guide) is
  to keep the keys in "environment variables" on your server. If you do paste
  them into the CONFIG block below, make sure this file NEVER goes into your
  public GitHub repo.

  Needs nothing extra installed -- it only uses Python's built-in tools.
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
# Your Anthropic API key (starts with "sk-ant-...") from console.anthropic.com
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "PASTE_YOUR_ANTHROPIC_KEY_HERE")

# Your Resend API key (starts with "re_...") -- you already use Resend for the site
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "PASTE_YOUR_RESEND_KEY_HERE")

# The "from" address -- must be on a domain you've verified in Resend
# (something like agent@dangerskycollectibles.com)
FROM_EMAIL = os.environ.get("DANGERSKY_FROM_EMAIL", "agent@dangerskycollectibles.com")

# Where YOU read the drafts. Your personal inbox is perfect.
TO_EMAIL = os.environ.get("DANGERSKY_REVIEW_EMAIL", "PASTE_YOUR_REVIEW_EMAIL_HERE")

# Which Claude model to use. Sonnet 4.6 is the workhorse -- smart and affordable.
MODEL = "claude-sonnet-4-6"
# =====================================================================


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BRIEF_PATH = os.path.join(SCRIPT_DIR, "dangersky_brand_brief.md")


def load_brief():
    """Load the brand brief -- the agent's brain."""
    try:
        with open(BRIEF_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        sys.exit(
            "ERROR: Could not find the brand brief at %s\n"
            "Put dangersky_brand_brief.md in the SAME folder as this script."
            % BRIEF_PATH
        )


# The job for today. This is what makes it the LANE 2 agent specifically.
TASK_PROMPT = """You are operating right now as the LANE 2 -- Home Turf (Community/Content) Agent for DangerSky Collectibles. Follow PART A (the core) and the LANE 2 MODULE of the brand brief above. Ignore the Lane 1 and Lane 3 modules for this task.

Produce today's batch of DRAFTS for Justin to review and post himself. Remember: you draft, Justin posts. Nothing here is auto-published.

Generate exactly this, clearly separated with headers:

1) THREE community-group post drafts -- for the fan communities Justin is part of (Pokemon GO especially, plus retro / gaming / Star Wars where it fits). Honor the 90/10 rule: each should be genuinely useful or fun to that community FIRST, with the shirt as a natural mention, not a hard sell. For each, note which community it's aimed at and a one-line reminder of that group's etiquette.

2) TWO posts for DangerSky's OWN social (Facebook Page / Instagram) -- full catalog allowed here, franchises included. On-brand voice, eye-catching, each ending with a clear path to dangerskycollectibles.com.

3) ONE short blog post idea + a 2-sentence hook -- SEO-friendly, tied to a fandom or nostalgia angle, pointing back to a product theme.

Keep Justin's voice: direct, casual, enthusiast-to-enthusiast, never corporate. Make everything copy-paste ready. If anything would need a judgment call from Justin, flag it briefly at the end under "FLAGGED FOR JUSTIN."
"""


def call_claude(brief):
    """Ask Claude to generate the drafts. Returns the text."""
    payload = {
        "model": MODEL,
        "max_tokens": 3000,
        "system": brief,
        "messages": [{"role": "user", "content": TASK_PROMPT}],
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
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit("ERROR talking to Claude API: %s %s" % (e.code, e.read().decode("utf-8")))
    except Exception as e:
        sys.exit("ERROR talking to Claude API: %s" % e)

    parts = [b.get("text", "") for b in body.get("content", []) if b.get("type") == "text"]
    return "\n".join(parts).strip()


def send_email(subject, body_text):
    """Email the drafts to Justin via Resend so he can review on his phone."""
    safe = body_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = (
        "<div style='font-family:sans-serif;white-space:pre-wrap;"
        "font-size:15px;line-height:1.5'>" + safe + "</div>"
    )
    payload = {
        "from": "DangerSky Lane 2 Agent <%s>" % FROM_EMAIL,
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
    print("[%s] Lane 2 agent starting..." % today)

    brief = load_brief()
    drafts = call_claude(brief)

    # Always save a local backup in case the email has a hiccup
    backup = os.path.join(SCRIPT_DIR, "lane2_drafts_%s.txt" % today)
    with open(backup, "w", encoding="utf-8") as f:
        f.write(drafts)
    print("Saved backup to", backup)

    send_email("DangerSky drafts to review -- %s" % today, drafts)
    print("Done.")


if __name__ == "__main__":
    main()
