"""Daily "[Date] - Interview Stages Summary" email.

Fetches the three trackr trackers (Hong Kong / US / UK finance summer
internships), diffs against the last snapshot to find same-day movements,
and emails a digest via Resend:

  1. Stage movements today, by region (old stage -> new stage, new
     programmes, process changes)
  2. Current pipeline, by region -> by stage -> programmes
  3. Application deadline countdown (upcoming closing dates, D-n)

The snapshot (data/trackr_snapshot.json) is only rewritten after a
successful send, so a failed send never swallows a movement: it will be
reported again on the next successful run.

    RESEND_API_KEY=... python3 scripts/daily_stage_email.py
    python3 scripts/daily_stage_email.py --dry-run    # print HTML, no email
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from zoneinfo import ZoneInfo

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.trackr_client import TRACKERS, fetch_all  # noqa: E402

logger = logging.getLogger(__name__)

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "data" / "trackr_snapshot.json"
RESEND_URL = "https://api.resend.com/emails"
EMAIL_FROM = os.environ.get("STAGE_EMAIL_FROM", "Trackr Daily <noreply@whalestreet.ai>")
EMAIL_TO = os.environ.get("STAGE_EMAIL_TO", "dylanlee20@outlook.com")
LOCAL_TZ = ZoneInfo("Asia/Hong_Kong")

REGION_ORDER = [t["region"] for t in TRACKERS]

# Canonical ordering for pipeline stages; unknown stages sort after these.
STAGE_ORDER = [
    "Applications Open", "Online Test", "HireVue", "Video Interview",
    "First Round", "Second Round", "Assessment Centre", "Superday",
    "Final Round", "Offers Out",
]

MAX_COUNTDOWN_ROWS = 30


# ---------------------------------------------------------------- snapshot

def load_snapshot() -> Dict[str, Dict]:
    if not SNAPSHOT_PATH.exists():
        return {}
    try:
        return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8")).get("programmes", {})
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("snapshot unreadable (%s); treating as first run", e)
        return {}


def save_snapshot(programmes: List[Dict]) -> None:
    payload = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "programmes": {
            p["external_id"]: {
                "company": p["company"],
                "position": p["position"],
                "region": p["region"],
                "current_stage": p["current_stage"],
                "process": p["process"],
                "closing_date": p["closing_date"],
            }
            for p in programmes
        },
    }
    SNAPSHOT_PATH.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n",
                             encoding="utf-8")


# ---------------------------------------------------------------- diffing

def diff_movements(programmes: List[Dict], previous: Dict[str, Dict]) -> List[Dict]:
    """One entry per programme whose stage/process changed or that is new."""
    movements = []
    for p in programmes:
        old = previous.get(p["external_id"])
        if old is None:
            if previous:  # skip "everything is new" noise on the first run
                movements.append({**p, "change": "new", "old": None})
            continue
        if (old.get("current_stage") or None) != p["current_stage"]:
            movements.append({**p, "change": "stage",
                              "old": old.get("current_stage")})
        elif (old.get("process") or None) != p["process"]:
            movements.append({**p, "change": "process",
                              "old": old.get("process")})
    return movements


# ---------------------------------------------------------------- rendering

def _esc(s) -> str:
    return html.escape(str(s or ""))


def _label(p: Dict) -> str:
    return f"<b>{_esc(p['company'])}</b> · {_esc(p['position'])}"


def _stage_sort_key(stage: str):
    try:
        return (STAGE_ORDER.index(stage), stage)
    except ValueError:
        return (len(STAGE_ORDER), stage)


def _section(title: str, body: str) -> str:
    return (f"<h2 style='font-size:16px;color:#1e3a8a;border-bottom:2px solid "
            f"#dbeafe;padding-bottom:6px;margin:28px 0 10px'>{title}</h2>{body}")


def _region_header(region: str) -> str:
    return (f"<h3 style='font-size:14px;color:#111827;background:#eff6ff;"
            f"padding:6px 10px;border-radius:6px;margin:16px 0 8px'>"
            f"{_esc(region)}</h3>")


def render_movements(movements: List[Dict], first_run: bool) -> str:
    if first_run:
        return ("<p style='color:#6b7280'>Baseline established today. "
                "Movements will appear starting tomorrow.</p>")
    if not movements:
        return "<p style='color:#6b7280'>No stage movements today.</p>"
    parts = []
    for region in REGION_ORDER:
        rows = [m for m in movements if m["region"] == region]
        if not rows:
            continue
        items = []
        for m in rows:
            if m["change"] == "new":
                detail = "<span style='color:#166534;font-weight:600'>NEW on tracker</span>"
                if m["current_stage"]:
                    detail += f" · stage: {_esc(m['current_stage'])}"
            elif m["change"] == "stage":
                detail = (f"stage: {_esc(m['old'] or 'none')} "
                          f"&rarr; <b style='color:#b91c1c'>{_esc(m['current_stage'] or 'none')}</b>")
            else:
                detail = (f"process: {_esc(m['old'] or 'none')} "
                          f"&rarr; <b>{_esc(m['process'] or 'none')}</b>")
            items.append(f"<li style='margin:4px 0'>{_label(m)}<br>"
                         f"<span style='font-size:13px'>{detail}</span></li>")
        parts.append(_region_header(region) +
                     f"<ul style='padding-left:18px;margin:4px 0'>{''.join(items)}</ul>")
    return "".join(parts)


def render_pipeline(programmes: List[Dict]) -> str:
    parts = []
    for region in REGION_ORDER:
        staged = [p for p in programmes
                  if p["region"] == region and p["current_stage"]]
        if not staged:
            continue
        stages: Dict[str, List[Dict]] = {}
        for p in staged:
            stages.setdefault(p["current_stage"], []).append(p)
        rows = []
        for stage in sorted(stages, key=_stage_sort_key):
            plist = "".join(
                f"<li style='margin:2px 0'>{_label(p)}"
                + (f" <span style='color:#6b7280;font-size:12px'>({_esc(p['process'])})</span>"
                   if p["process"] else "")
                + "</li>"
                for p in stages[stage])
            rows.append(f"<p style='margin:8px 0 2px;font-weight:600;font-size:13px;"
                        f"color:#374151'>{_esc(stage)} ({len(stages[stage])})</p>"
                        f"<ul style='padding-left:18px;margin:2px 0'>{plist}</ul>")
        parts.append(_region_header(region) + "".join(rows))
    if not parts:
        return "<p style='color:#6b7280'>No programmes currently report a stage.</p>"
    return "".join(parts)


def render_countdown(programmes: List[Dict], today) -> str:
    parts = []
    for region in REGION_ORDER:
        upcoming = []
        for p in programmes:
            if p["region"] != region or not p["closing_date"]:
                continue
            try:
                closing = datetime.strptime(p["closing_date"], "%Y-%m-%d").date()
            except ValueError:
                continue
            days = (closing - today).days
            if days >= 0:
                upcoming.append((days, closing, p))
        if not upcoming:
            continue
        upcoming.sort(key=lambda t: (t[0], t[2]["company"]))
        shown = upcoming[:MAX_COUNTDOWN_ROWS]
        items = []
        for days, closing, p in shown:
            color = "#b91c1c" if days <= 7 else ("#854d0e" if days <= 14 else "#374151")
            badge = "closes TODAY" if days == 0 else f"D-{days}"
            items.append(
                f"<li style='margin:3px 0'>"
                f"<b style='color:{color}'>{badge}</b> · "
                f"{closing.strftime('%b %d')} · {_label(p)}</li>")
        more = ""
        if len(upcoming) > len(shown):
            more = (f"<p style='color:#6b7280;font-size:12px'>"
                    f"+{len(upcoming) - len(shown)} more with later deadlines</p>")
        parts.append(_region_header(region) +
                     f"<ul style='padding-left:18px;margin:4px 0'>{''.join(items)}</ul>" + more)
    if not parts:
        return "<p style='color:#6b7280'>No upcoming deadlines on record.</p>"
    return "".join(parts)


def build_email(programmes: List[Dict], movements: List[Dict],
                first_run: bool, today) -> str:
    counts = " · ".join(
        f"{region} {sum(1 for p in programmes if p['region'] == region)}"
        for region in REGION_ORDER)
    return f"""
<div style="font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;
            max-width:680px;margin:0 auto;color:#111827;font-size:14px">
  <h1 style="font-size:19px;color:#1e3a8a;margin-bottom:2px">
    Interview Stages Summary · {today.strftime('%b %d, %Y')}</h1>
  <p style="color:#6b7280;margin-top:2px;font-size:13px">
    Finance summer internships (2027 cycle) · {counts} programmes tracked</p>
  {_section('1 · Stage Movements Today', render_movements(movements, first_run))}
  {_section('2 · Current Pipeline by Region', render_pipeline(programmes))}
  {_section('3 · Application Deadline Countdown', render_countdown(programmes, today))}
  <p style="color:#9ca3af;font-size:11px;margin-top:30px">
    Source: the-trackr.com · generated by job-tracker/scripts/daily_stage_email.py</p>
</div>"""


# ---------------------------------------------------------------- sending

def send_email(subject: str, html_body: str) -> None:
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not set")
    resp = requests.post(
        RESEND_URL,
        json={"from": EMAIL_FROM, "to": [EMAIL_TO],
              "subject": subject, "html": html_body},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    if resp.status_code >= 300:
        raise RuntimeError(f"Resend error {resp.status_code}: {resp.text[:300]}")
    logger.info("email sent to %s (id %s)", EMAIL_TO, resp.json().get("id"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="print the HTML instead of sending")
    args = parser.parse_args()

    today = datetime.now(LOCAL_TZ).date()
    programmes = fetch_all()
    if len(programmes) < 100:
        raise RuntimeError(f"only {len(programmes)} programmes fetched; aborting")

    previous = load_snapshot()
    first_run = not previous
    movements = diff_movements(programmes, previous)
    logger.info("%d programmes, %d movements (first_run=%s)",
                len(programmes), len(movements), first_run)

    subject = f"[{today.strftime('%Y-%m-%d')}] - Interview Stages Summary"
    body = build_email(programmes, movements, first_run, today)

    if args.dry_run:
        print(subject)
        print(body)
        return

    send_email(subject, body)
    save_snapshot(programmes)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
