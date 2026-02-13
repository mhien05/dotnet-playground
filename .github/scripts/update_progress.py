#!/usr/bin/env python3
"""
update_progress.py - Tự động cập nhật bảng tiến độ học tập trong README.md

Logic:
  - Folder KHÔNG tồn tại           → ⬜ Chưa bắt đầu
  - Folder tồn tại + có file DONE  → ✅ Hoàn thành
  - Folder tồn tại + có nội dung   → 🔄 Đang học
  - Folder tồn tại + rỗng          → ⬜ Chưa bắt đầu

Cách đánh dấu "Hoàn thành": tạo file DONE (hoặc DONE.md) trong folder bài học.
"""

import json
import os
import re
from datetime import datetime, timezone, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(REPO_ROOT, ".github", "progress.json")
README_PATH = os.path.join(REPO_ROOT, "README.md")

# Các file/folder hệ thống cần bỏ qua khi đếm nội dung
IGNORE_FILES = {".gitkeep", ".DS_Store", "Thumbs.db", "DONE", "DONE.md"}


def has_meaningful_content(folder_path: str) -> bool:
    """Kiểm tra folder có file nội dung thực sự không (trừ DONE, .gitkeep, v.v.)."""
    if not os.path.isdir(folder_path):
        return False
    for item in os.listdir(folder_path):
        if item not in IGNORE_FILES and not item.startswith("."):
            return True
    return False


def has_done_marker(folder_path: str) -> bool:
    """Kiểm tra folder có file DONE hoặc DONE.md không (không phân biệt hoa thường)."""
    if not os.path.isdir(folder_path):
        return False
    for item in os.listdir(folder_path):
        if item.upper() in {"DONE", "DONE.MD"}:
            return True
    return False


def get_status(folder_path: str) -> tuple[str, str]:
    """Trả về (icon, label) trạng thái dựa trên nội dung folder."""
    if not os.path.isdir(folder_path):
        return "⬜", "Chưa bắt đầu"
    if has_done_marker(folder_path):
        return "✅", "Hoàn thành"
    if has_meaningful_content(folder_path):
        return "🔄", "Đang học"
    return "⬜", "Chưa bắt đầu"


def build_progress_bar(completed: int, total: int, width: int = 20) -> str:
    """Tạo progress bar dạng text."""
    filled = round(width * completed / total) if total > 0 else 0
    bar = "█" * filled + "░" * (width - filled)
    percent = round(100 * completed / total) if total > 0 else 0
    return f"[{bar}] {completed}/{total} chủ đề ({percent}%)"


def main():
    # Đọc config
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    topics = config["topics"]

    # Tính trạng thái từng topic
    rows = []
    completed_count = 0
    in_progress_count = 0

    for topic in topics:
        folder_path = os.path.join(REPO_ROOT, topic["folder"])
        icon, label = get_status(folder_path)

        if icon == "✅":
            completed_count += 1
        elif icon == "🔄":
            in_progress_count += 1

        # Pad các cột cho đẹp
        tid = str(topic["id"]).ljust(2)
        week = topic["week"].ljust(10)
        title = topic["title"].ljust(52)
        status = f"{icon} {label}".ljust(19)

        rows.append(f"| {tid} | {week} | {title} | {status} |         |")

    # Tạo timestamp (UTC+7)
    vn_tz = timezone(timedelta(hours=7))
    now = datetime.now(vn_tz).strftime("%d/%m/%Y %H:%M (UTC+7)")

    # Build bảng mới
    table_header = (
        "| #  | Tuần       | Chủ đề"
        + " " * 45
        + "| Trạng thái          | Ghi chú |"
    )
    table_separator = (
        "|----|------------|"
        + "-" * 54
        + "|---------------------|---------|"
    )

    progress_bar = build_progress_bar(completed_count, len(topics))

    new_section = f"""<!-- PROGRESS:START - Tự động cập nhật bởi GitHub Actions, KHÔNG sửa tay phần này -->
## 📊 Tracking Tiến Độ Học Tập

> **Cập nhật lần cuối:** `{now}`

{table_header}
{table_separator}
{chr(10).join(rows)}

### 📈 Tổng quan

```text
Tiến độ: {progress_bar}
```

### Chú thích

| Icon | Ý nghĩa        |
|------|-----------------|
| ⬜   | Chưa bắt đầu   |
| 🔄   | Đang học        |
| ✅   | Hoàn thành      |
<!-- PROGRESS:END -->"""

    # Đọc README hiện tại
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    # Thay thế phần giữa markers
    pattern = r"<!-- PROGRESS:START.*?-->.*?<!-- PROGRESS:END -->"
    if re.search(pattern, readme, re.DOTALL):
        new_readme = re.sub(pattern, new_section, readme, flags=re.DOTALL)
    else:
        # Nếu chưa có markers, thêm vào cuối
        new_readme = readme.rstrip() + "\n\n---\n\n" + new_section + "\n"

    # Ghi lại
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_readme)

    # In summary
    print(f"✅ Đã cập nhật README.md")
    print(f"   📊 Hoàn thành: {completed_count}/{len(topics)}")
    print(f"   🔄 Đang học:   {in_progress_count}")
    print(f"   ⬜ Chưa bắt đầu: {len(topics) - completed_count - in_progress_count}")


if __name__ == "__main__":
    main()
