#!/usr/bin/env python3
"""
Quark - GitHub Email Sorter for Proton Mail
Connects via Proton Bridge IMAP, reads GitHub notification emails,
and sorts them into per-repository folders automatically.
"""

import imaplib
import email
import re
import logging
import os
from email.header import decode_header
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the same directory as the script
load_dotenv(Path(__file__).parent / ".env")

# ── Configuration ──────────────────────────────────────────────────────────────
IMAP_HOST            = os.getenv("IMAP_HOST", "127.0.0.1")
IMAP_PORT            = int(os.getenv("IMAP_PORT", 1143))
USERNAME             = os.getenv("PROTON_USERNAME")
PASSWORD             = os.getenv("PROTON_BRIDGE_PASSWORD")
GITHUB_FOLDER_PREFIX = os.getenv("GITHUB_FOLDER_PREFIX", "GitHub")
INBOX                = "INBOX"
# ──────────────────────────────────────────────────────────────────────────────

# Validate required config
if not USERNAME or not PASSWORD:
    raise ValueError("PROTON_USERNAME and PROTON_BRIDGE_PASSWORD must be set in your .env file")

# ── Logging ───────────────────────────────────────────────────────────────────
log_path = Path(__file__).parent / "logs" / "quark.log"
log_path.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        RotatingFileHandler(
            log_path,
            maxBytes=1_000_000,  # 1 MB per file
            backupCount=3        # Keep up to 4 files: quark.log + .1 .2 .3
        ),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)
# ──────────────────────────────────────────────────────────────────────────────


def decode_str(value):
    """Decode email header strings."""
    if value is None:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(encoding or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def extract_repo_from_email(msg):
    """
    Try multiple strategies to identify the GitHub repository from an email.
    Returns (owner, repo) tuple or (None, None) if not found.
    """
    # Strategy 1: List-ID header (most reliable)
    # Format: <repo.owner.github.com>
    list_id = msg.get("List-ID", "")
    match = re.search(r"([\w.-]+)\.([\w.-]+)\.github\.com", list_id)
    if match:
        repo, owner = match.group(1), match.group(2)
        return owner, repo

    # Strategy 2: Subject line
    # GitHub subjects look like: [owner/repo] Issue title
    subject = decode_str(msg.get("Subject", ""))
    match = re.search(r"\[([^/\]]+)/([^\]]+)\]", subject)
    if match:
        owner, repo = match.group(1).strip(), match.group(2).strip()
        return owner, repo

    # Strategy 3: From header
    from_header = decode_str(msg.get("From", ""))
    match = re.search(r"([\w.-]+)/([\w.-]+)", from_header)
    if match:
        return match.group(1), match.group(2)

    return None, None


def is_github_email(msg):
    """Check if this email originated from GitHub."""
    from_header = decode_str(msg.get("From", "")).lower()
    sender = msg.get("X-GitHub-Sender", "")
    return (
        "github.com" in from_header
        or "noreply@github.com" in from_header
        or sender != ""
    )


def ensure_folder_exists(imap, folder_path):
    """Create an IMAP folder (and any missing parent folders) if needed."""
    parts = folder_path.split("/")
    for i in range(1, len(parts) + 1):
        partial = "/".join(parts[:i])
        result, _ = imap.select(f'"{partial}"')
        if result != "OK":
            log.info(f"Creating folder: {partial}")
            imap.create(f'"{partial}"')
            imap.subscribe(f'"{partial}"')


def sanitize_name(name):
    """Remove characters that are invalid in IMAP folder names."""
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


def sort_github_emails():
    log.info("Quark starting — connecting to Proton Bridge IMAP...")
    try:
        imap = imaplib.IMAP4(IMAP_HOST, IMAP_PORT)
        imap.login(USERNAME, PASSWORD)
    except Exception as e:
        log.error(f"Failed to connect to IMAP: {e}")
        return

    imap.select(INBOX)

    result, data = imap.search(None, "UNSEEN")
    if result != "OK" or not data[0]:
        log.info("No new emails to process.")
        imap.logout()
        return

    email_ids = data[0].split()
    log.info(f"Found {len(email_ids)} unseen email(s) to check.")

    moved = 0
    skipped = 0

    for eid in email_ids:
        result, msg_data = imap.fetch(eid, "(RFC822)")
        if result != "OK":
            continue

        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        if not is_github_email(msg):
            skipped += 1
            continue

        owner, repo = extract_repo_from_email(msg)
        if not owner or not repo:
            log.warning(f"Could not determine repo for: {decode_str(msg.get('Subject', '(no subject)'))}")
            skipped += 1
            continue

        owner = sanitize_name(owner)
        repo  = sanitize_name(repo)
        target_folder = f"{GITHUB_FOLDER_PREFIX}/{owner}/{repo}"

        ensure_folder_exists(imap, target_folder)

        # Copy to target folder then mark original for deletion (= move)
        copy_result, _ = imap.copy(eid, f'"{target_folder}"')
        if copy_result == "OK":
            imap.store(eid, "+FLAGS", "\\Deleted")
            log.info(f"Moved '{decode_str(msg.get('Subject', ''))}' → {target_folder}")
            moved += 1
        else:
            log.error(f"Failed to copy email to {target_folder}")

    imap.expunge()
    log.info(f"Done. Moved {moved} email(s), skipped {skipped} non-GitHub email(s).")
    imap.logout()


if __name__ == "__main__":
    sort_github_emails()
