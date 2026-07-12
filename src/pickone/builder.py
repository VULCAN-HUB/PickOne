# -*- coding: utf-8 -*-
"""HTML 빌드 — 템플릿 치환. 항상 단일 .html (분할·zip 없음)."""
import json
import os
from typing import Dict, List

from .scanner import Item
from .preview import PreviewResult

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template", "selector.html")


def item_size(pv: PreviewResult, uid: int) -> int:
    return len(pv.thumbs.get(uid, "")) + len(pv.larges.get(uid, ""))


def estimate_bytes(items: List[Item], pv: PreviewResult) -> int:
    return sum(item_size(pv, i.uid) for i in items) + 30_000  # 템플릿 고정분


def _render(template: str, title: str, goal: int, notice: str,
            items: List[Item], pv: PreviewResult) -> str:
    data = {
        "title": title,
        "goal": goal,
        "notice": notice,
        "items": [
            {"u": it.uid, "d": it.display, "t": pv.thumbs.get(it.uid, ""),
             "dt": pv.exif_dts.get(it.uid, "")}
            for it in items
        ],
    }
    large = {str(it.uid): pv.larges.get(it.uid, "") for it in items}
    # </script> 가 data 안에 등장하지 않도록 이스케이프 (base64라 실제론 없음, 방어용)
    dj = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    lj = json.dumps(large, ensure_ascii=False).replace("</", "<\\/")
    html = template.replace("{{DATA_JSON}}", dj).replace("{{LARGE_JSON}}", lj)
    return html.replace("{{TITLE}}", title)


def build_gallery(items: List[Item], pv: PreviewResult, title: str, goal: int,
                  notice: str, out_dir: str) -> List[Dict[str, object]]:
    """선택분을 단일 HTML로 빌드. 반환: [{html, count, bytes}] (항상 길이 1)."""
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()
    ok_items = [i for i in items if i.uid in pv.thumbs]
    os.makedirs(out_dir, exist_ok=True)
    html = _render(template, title, goal, notice, ok_items, pv)
    html_path = os.path.join(out_dir, title + ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return [{"html": html_path, "count": len(ok_items),
             "bytes": os.path.getsize(html_path)}]
