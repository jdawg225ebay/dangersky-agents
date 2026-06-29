#!/bin/bash
# DangerSky - one-time setup: makes keys permanent + schedules all 4 agents on cron.
# Run this AFTER the keys are already set in your current session (export/read -rs).
# Safe to re-run anytime -- it overwrites cleanly and won't duplicate cron entries.
set -e

mkdir -p ~/agents

# 1) Save current session's keys permanently to a private env file
{
  echo "export ANTHROPIC_API_KEY='$ANTHROPIC_API_KEY'"
  echo "export RESEND_API_KEY='$RESEND_API_KEY'"
  echo "export DANGERSKY_FROM_EMAIL='$DANGERSKY_FROM_EMAIL'"
  echo "export DANGERSKY_REVIEW_EMAIL='$DANGERSKY_REVIEW_EMAIL'"
} > ~/agents/.env
chmod 600 ~/agents/.env

# 2) Make every future terminal session auto-load it
grep -qxF 'source ~/agents/.env' ~/.bashrc || echo 'source ~/agents/.env' >> ~/.bashrc

# 3) Schedule all 4 agents on cron, sourcing the env file each run
H=$HOME
PY=$(command -v python3)
( crontab -l 2>/dev/null | grep -v 'agents/lane[1-4]_agent.py' ; cat << CRON
0 9 * * * . $H/agents/.env && $PY $H/agents/lane1_agent.py >> $H/agents/lane1.log 2>&1
0 9,13,18 * * * . $H/agents/.env && $PY $H/agents/lane2_agent.py >> $H/agents/lane2.log 2>&1
0 10 * * * . $H/agents/.env && $PY $H/agents/lane3_agent.py >> $H/agents/lane3.log 2>&1
0 11 * * * . $H/agents/.env && $PY $H/agents/lane4_agent.py >> $H/agents/lane4.log 2>&1
CRON
) | crontab -

echo "---- DONE ----"
echo "Saved variable names:"
grep -o '^export [A-Z_]*' ~/agents/.env
echo "Installed cron jobs:"
crontab -l
