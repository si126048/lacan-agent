"""Chat file parsers for WeChat export formats."""

from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

RETURN_SYMBOL = "\u23ce"
SEPARATOR_RE = re.compile(r"^-{10,}$")
TIMESTAMP_RE = re.compile(r"^\[(\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2})\]$")
MESSAGE_RE = re.compile(r"^【(.+?)】：(.*)$")


def load_participant_messages(path: str | Path) -> list[str]:
    """Load messages from participant_texts/*.txt format.

    Each line is one message, terminated by ⏎ (U+238E).
    Returns list of message strings with ⏎ stripped.
    """
    text = read_text(path)
    messages = []
    for line in text.splitlines():
        msg = line.rstrip().removesuffix(RETURN_SYMBOL).strip()
        if msg:
            messages.append(msg)
    return messages


def read_text(path: str | Path) -> str:
    """Read exports with UTF-8 first and GB18030 fallback."""
    p = Path(path)
    try:
        return p.read_text(encoding='utf-8-sig')
    except UnicodeDecodeError:
        return p.read_text(encoding='gb18030')


def stable_message_id(source_id: str, index: int, content: str) -> str:
    digest = hashlib.sha256(f'{source_id}:{index}:{content}'.encode('utf-8')).hexdigest()[:16]
    return f'msg_{digest}'


def load_normalized_messages(path: str | Path, source_id: str | None = None) -> list[dict]:
    """Return stable, serializable messages for profile artifacts."""
    source_id = source_id or Path(path).stem
    parsed = parse_wechat_chat(path)
    messages = [item.content for item in parsed] if parsed else load_participant_messages(path)
    raw_text = read_text(path)
    cursor = 0
    normalized = []
    for i, content in enumerate(messages):
        start = raw_text.find(content, cursor)
        if start < 0:
            start = cursor
        normalized.append({
            'message_id': stable_message_id(source_id, i, content),
            'source_id': source_id,
            'index': i,
            'content': content,
            'char_start': start,
            'char_end': start + len(content),
        })
        cursor = start + len(content)
    return normalized


@dataclass
class ChatMessage:
    sender: str
    content: str
    timestamp: datetime | None = None


def parse_wechat_chat(path: str | Path) -> list[ChatMessage]:
    """Parse WeChat multi-line export format from E:\\archive\\chat_*.txt.

    Format:
        -----------------------
        [YY-MM-DD HH:MM]
        -----------------------
        【sender】：content⏎
    """
    text = read_text(path)
    lines = text.splitlines()

    messages: list[ChatMessage] = []
    current_ts: datetime | None = None
    sep_count = 0

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        if SEPARATOR_RE.match(stripped):
            sep_count += 1
            continue

        ts_match = TIMESTAMP_RE.match(stripped)
        if ts_match and sep_count >= 1:
            try:
                current_ts = datetime.strptime(ts_match.group(1), "%y-%m-%d %H:%M")
            except ValueError:
                pass
            sep_count = 0
            continue

        sep_count = 0

        msg_match = MESSAGE_RE.match(stripped)
        if msg_match:
            sender = msg_match.group(1)
            content = msg_match.group(2).removesuffix(RETURN_SYMBOL).strip()

            if sender == "系统":
                continue

            messages.append(ChatMessage(sender=sender, content=content, timestamp=current_ts))

    return messages
