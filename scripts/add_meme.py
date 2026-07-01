#!/usr/bin/env python3
"""
Semi-automatic meme ingest for Still Saying Good Morning.

Usage:
  1. Drop today's image into photos/inbox/ (any .jpg / .jpeg / .png name).
  2. Run:  python3 scripts/add_meme.py --time 10:16
     Or:    python3 scripts/add_meme.py --time 10:16 --date 2026-06-07
  3. GitHub Desktop → Commit → Push.

The script renames the image, appends archive.json, and removes the inbox file.
It does not push to GitHub (semi-automatic).
"""

from __future__ import annotations

import argparse
import calendar
import json
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_PATH = ROOT / "archive.json"
INBOX_DIR = ROOT / "photos" / "inbox"
PHOTOS_DIR = ROOT / "photos"

MONTH_NUM = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}
MONTH_ABBR = {v: k for k, v in MONTH_NUM.items()}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def parse_time(value: str) -> str:
    m = TIME_RE.match(value.strip())
    if not m:
        raise ValueError(f"时间格式不对: {value!r}，请用 24 小时制，例如 10:16")
    return f"{int(m.group(1)):02d}:{m.group(2)}"


def parse_date(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"日期格式不对: {value!r}，请用 YYYY-MM-DD，例如 2026-06-07") from exc


def load_archive() -> dict:
    with ARCHIVE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def save_archive(archive: dict) -> None:
    with ARCHIVE_PATH.open("w", encoding="utf-8") as f:
        json.dump(archive, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _month_key(label: str) -> tuple[int, int]:
    """(year, month) sort key parsed from a month label like 'Jul 2026'."""
    parts = label.split()
    return (int(parts[1]), MONTH_NUM[parts[0]])


def ensure_month(archive: dict, year: int, month: int) -> tuple[str, bool]:
    """Return (month_id, created). Auto-creates the month in archive.json if it
    doesn't exist yet, following the exact same format as existing months so the
    website renders it without any other change. Works for any future month."""
    for m in archive["months"]:
        parts = m["label"].split()
        if len(parts) == 2 and MONTH_NUM.get(parts[0]) == month and int(parts[1]) == year:
            return m["id"], False

    mon = MONTH_ABBR[month]
    new_id = f"{mon.lower()}{year % 100:02d}"
    existing_ids = {m["id"] for m in archive["months"]}
    base, n = new_id, 2
    while new_id in existing_ids:
        new_id = f"{base}_{n}"
        n += 1

    days = calendar.monthrange(year, month)[1]
    new_month = {
        "id": new_id,
        "label": f"{mon} {year}",
        "ariaLabel": f"{year}年{month}月",
        "days": days,
        "cols31": days == 31,
    }

    key = (year, month)

    # months[] is ordered oldest -> newest.
    pos = len(archive["months"])
    for i, m in enumerate(archive["months"]):
        if _month_key(m["label"]) > key:
            pos = i
            break
    archive["months"].insert(pos, new_month)

    # displayOrder[] is ordered newest -> oldest.
    id_key = {m["id"]: _month_key(m["label"]) for m in archive["months"]}
    dpos = len(archive["displayOrder"])
    for i, mid in enumerate(archive["displayOrder"]):
        if id_key.get(mid, (0, 0)) < key:
            dpos = i
            break
    archive["displayOrder"].insert(dpos, new_id)

    return new_id, True


def make_label(year: int, month: int, day: int, time_str: str) -> str:
    mon = MONTH_ABBR[month]
    if year == 2024:
        return f"{day} {mon} {year} {time_str}"
    return f"{mon} {day} {year} {time_str}"


def photo_filename(d: date) -> str:
    return f"{d.year % 100:02d}{d.month:02d}{d.day:02d}.jpg"


def chron_index(archive: dict) -> dict[str, int]:
    return {m["id"]: i for i, m in enumerate(archive["months"])}


CONFORMING_RE = re.compile(r"^\d{6}\.jpg$", re.IGNORECASE)


def pick_inbox_image(explicit: Path | None, known_photos: set[str], target_name: str) -> Path:
    if explicit:
        if not explicit.is_file():
            raise FileNotFoundError(f"找不到图片: {explicit}")
        if explicit.suffix.lower() not in IMAGE_EXTS:
            raise ValueError(f"不支持的图片格式: {explicit.suffix}")
        return explicit

    if not INBOX_DIR.is_dir():
        INBOX_DIR.mkdir(parents=True, exist_ok=True)

    # 0) If the user already named the file for the target date, use it directly.
    #    This wins over any unrelated leftover images sitting in photos/.
    target_in_photos = PHOTOS_DIR / target_name
    if target_in_photos.is_file() and target_name not in known_photos:
        return target_in_photos

    # 1) Prefer photos/inbox/
    candidates = [
        p for p in INBOX_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS and not p.name.startswith(".")
    ]
    # 2) Otherwise, look in photos/ for an image that is NOT yet recorded in
    #    archive.json (a freshly pasted random-named drop), while never touching
    #    the hundreds of existing memes (which are all listed in archive.json).
    if not candidates:
        candidates = [
            p for p in PHOTOS_DIR.iterdir()
            if p.is_file()
            and p.suffix.lower() in IMAGE_EXTS
            and not p.name.startswith(".")
            and p.name not in known_photos
        ]

    if not candidates:
        raise FileNotFoundError(
            "没找到新图片。\n"
            "请把今天的 meme 粘贴到 photos/ 或 photos/inbox/ 文件夹里再运行。"
        )
    if len(candidates) > 1:
        names = ", ".join(p.name for p in sorted(candidates))
        raise RuntimeError(
            f"发现多张待处理图片 ({names})，请只留一张，或用 --file 指定路径。"
        )
    return candidates[0]


def entry_exists(archive: dict, month: str, day: int, photo: str) -> bool:
    for e in archive["entries"]:
        if e.get("photo") == photo or (e.get("month") == month and e.get("day") == day):
            return True
    return False


def add_meme(time_str: str, on_date: date, source: Path | None) -> dict:
    archive = load_archive()
    month_id, month_created = ensure_month(archive, on_date.year, on_date.month)
    photo = photo_filename(on_date)

    if entry_exists(archive, month_id, on_date.day, photo):
        raise RuntimeError(
            f"{on_date.isoformat()} 已有记录 ({photo})，未改动。"
            f"若要覆盖请先手动删除 archive.json 里对应条目。"
        )

    known_photos = {e.get("photo") for e in archive["entries"] if e.get("photo")}
    dest = PHOTOS_DIR / photo
    src = pick_inbox_image(source, known_photos, photo)
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

    removed_source = None
    if src.resolve() == dest.resolve():
        # User already pasted the file with the correct YYMMDD.jpg name; leave it
        # in place and just record it in archive.json.
        pass
    else:
        if dest.exists():
            raise RuntimeError(f"目标文件已存在: {dest}，未覆盖。")
        shutil.copy2(src, dest)
        # Remove the original drop (inbox file, or a freshly pasted file in
        # photos/), but never delete the renamed destination itself.
        in_inbox = src.parent.resolve() == INBOX_DIR.resolve()
        in_photos_root = src.parent.resolve() == PHOTOS_DIR.resolve()
        if in_inbox or in_photos_root:
            src.unlink()
            removed_source = src.name

    entry = {
        "month": month_id,
        "day": on_date.day,
        "photo": photo,
        "time": time_str,
        "label": make_label(on_date.year, on_date.month, on_date.day, time_str),
    }
    archive["entries"].append(entry)
    idx = chron_index(archive)
    archive["entries"].sort(key=lambda e: (idx[e["month"]], e["day"]))
    save_archive(archive)

    return {
        "entry": entry,
        "photo_path": dest,
        "removed_inbox": removed_source,
        "month_created": month_created,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Add today's meme to archive.json (semi-auto).")
    parser.add_argument("--time", required=True, help="发送时间，24 小时制，例如 10:16")
    parser.add_argument("--date", help="日期 YYYY-MM-DD，默认今天")
    parser.add_argument("--file", type=Path, help="图片路径；默认用 photos/inbox/ 里唯一一张")
    args = parser.parse_args()

    try:
        time_str = parse_time(args.time)
        on_date = parse_date(args.date)
        result = add_meme(time_str, on_date, args.file)
    except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    e = result["entry"]
    print("完成 ✓")
    if result.get("month_created"):
        print(f"  已自动新建月份: {e['month']}（{on_date.year} 年 {on_date.month} 月）")
    print(f"  图片: {result['photo_path'].relative_to(ROOT)}")
    print(f"  条目: {e['month']} day {e['day']}  {e['time']}  {e['label']}")
    print()
    print("下一步: GitHub Desktop → 勾选 archive.json 和 photos/ → Commit → Push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
