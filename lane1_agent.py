#!/usr/bin/env python3
"""
DangerSky Collectibles - LANE 1 AGENT (Money Lane: Brand Posts + Ad Proposals)
------------------------------------------------------------------------------
What it does, in plain English:
  1. Loads your brand brief (dangersky_brand_brief.md) -- the "brain."
  2. Writes a batch of BRAND-LED social posts (Instagram / Facebook / Pinterest)
     for the paid/account-linked lane -- original + generic-patriotic designs only.
  3. Drafts one or more AD-CAMPAIGN PROPOSALS for you to approve.
  4. Emails it all to you.

  >>> THE MONEY RULE <<<
  This agent NEVER spends money, launches an ad, or changes a budget on its own.
  It only PROPOSES. Every proposal waits for your explicit "yes" before anything
  runs. You are the only one who pulls the trigger on spend.

  >>> THE TWO TESTS (hard rules for this lane) <<<
  Nothing here may contain (1) franchise material (Pokemon, Star Wars, etc.) or
  (2) any politician / party / slogan. Generic patriotic (flag/eagle/"I Love
  America") is fine. Franchise + named-figure designs belong to Lanes 2 & 3 only.

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


TASK_PROMPT = """You are operating right now as the LANE 1 -- Money Lane (Paid + Account-Linked) Agent for DangerSky Collectibles. Follow PART A (the core) and the LANE 1 MODULE of the brand brief above.

HARD RULE -- every single thing you produce must pass BOTH tests: (1) IP-clean (no franchise material at all) and (2) politics-clean (no politician, party, or slogan). Generic patriotic is allowed. If a design would fail either test, do not use it here.

HARD RULE -- you never spend money. You only PROPOSE. Nothing you write launches or changes spend on its own.

Produce two clearly separated sections:

SECTION A -- BRAND-LED SOCIAL DRAFTS (for the approval queue)
Write 3 posts for DangerSky's paid/account-linked social (Instagram / Facebook / Pinterest). Brand aesthetic and original / inspired-by / generic-patriotic designs only. Eye-catching, on-brand voice, each ending with a clear path to dangerskycollectibles.com. Tailor each to its platform.

SECTION B -- AD-CAMPAIGN PROPOSAL(S) (for Justin's approval -- NOT auto-launched)
Draft 1-2 ad-campaign proposals. For EACH, state plainly:
  - WHAT: the campaign concept and the exact creative/design (confirm it passes both tests)
  - AUDIENCE: the fandom interest + buying-behavior targeting (target by interest + proven online buyers, NOT by politics)
  - SPEND: an exact suggested daily budget and total (e.g. $10/day for 14 days = $140)
  - DURATION: how long to run before judging it
  - GOAL: what result you expect and the number you'd watch (e.g. cost per click, cost per purchase)
  - WHY: one line on why this is worth testing
End Section B with: "AWAITING JUSTIN'S APPROVAL -- no spend happens until you say go."

Keep Justin's voice throughout: direct, casual, fan-to-fan, never corporate. If anything needs a judgment call, flag it under "FLAGGED FOR JUSTIN."
"""


def call_claude(brief):
    payload = {
        "model": MODEL,
        "max_tokens": 3500,
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
    safe = body_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = (
        "<div style='font-family:sans-serif;white-space:pre-wrap;"
        "font-size:15px;line-height:1.5'>" + safe + "</div>"
    )
    payload = {
        "from": "DangerSky Lane 1 Agent <%s>" % FROM_EMAIL,
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
            "User-Agent": "DangerSky-Agent/1.0",
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
    print("[%s] Lane 1 agent starting..." % today)

    brief = load_brief()
    output = call_claude(brief)

    backup = os.path.join(SCRIPT_DIR, "lane1_output_%s.txt" % today)
    with open(backup, "w", encoding="utf-8") as f:
        f.write(output)
    print("Saved backup to", backup)

    send_email("DangerSky Lane 1 -- posts + ad proposals to approve -- %s" % today, output)
    print("Done.")


if __name__ == "__main__":
    main()
