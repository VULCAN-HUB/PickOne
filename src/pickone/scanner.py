# -*- coding: utf-8 -*-
"""폴더/파일 재귀 수집 → 한 갤러리로 평탄화 → 표시명 충돌 해소 + uid 부여."""
import os
import unicodedata
from dataclasses import dataclass, field
from typing import List, Optional

PHOTO_EXTS = {
    ".jpg", ".jpeg", ".png", ".heic", ".heif", ".tif", ".tiff", ".webp", ".bmp",
    ".cr2", ".cr3", ".nef", ".arw", ".dng", ".orf", ".rw2", ".raf",
}
RAW_EXTS = {".cr2", ".cr3", ".nef", ".arw", ".dng", ".orf", ".rw2", ".raf"}


@dataclass
class Item:
    uid: int
    display: str
    path: str
    mtime: float = 0.0
    exif_dt: Optional[str] = None
    error: Optional[str] = field(default=None)  # 프리뷰 단계에서 실패 사유 기록


def _collect_files(paths: List[str]) -> List[str]:
    files = []
    for p in paths:
        p = os.path.abspath(p)
        if os.path.isfile(p):
            files.append(p)
        elif os.path.isdir(p):
            for root, _dirs, names in os.walk(p):
                for n in names:
                    files.append(os.path.join(root, n))
    return [f for f in files if os.path.splitext(f)[1].lower() in PHOTO_EXTS]


def scan(paths: List[str]) -> List[Item]:
    files = sorted(set(_collect_files(paths)),
                   key=lambda f: unicodedata.normalize("NFC", os.path.basename(f)).lower())

    # 1차: 기본 파일명 → 충돌 시 폴더명 접두 → 그래도 충돌 시 _2, _3 …
    counts = {}
    for f in files:
        base = unicodedata.normalize("NFC", os.path.basename(f))
        counts[base] = counts.get(base, 0) + 1

    used = set()
    items = []
    for i, f in enumerate(files, 1):
        base = unicodedata.normalize("NFC", os.path.basename(f))
        name = base
        if counts[base] > 1:
            folder = unicodedata.normalize("NFC", os.path.basename(os.path.dirname(f)))
            name = "{}_{}".format(folder, base) if folder else base
        if name in used:
            stem, ext = os.path.splitext(name)
            n = 2
            while "{}_{}{}".format(stem, n, ext) in used:
                n += 1
            name = "{}_{}{}".format(stem, n, ext)
        used.add(name)
        try:
            mtime = os.path.getmtime(f)
        except OSError:
            mtime = 0.0
        items.append(Item(uid=i, display=name, path=f, mtime=mtime))
    return items
