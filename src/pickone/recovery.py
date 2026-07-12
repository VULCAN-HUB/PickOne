# -*- coding: utf-8 -*-
"""회수 모드 — 결과 .json/텍스트 파싱, uid 우선 매칭(파일명 폴백), 평탄화 복사."""
import json
import os
import re
import shutil
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .scanner import Item, PHOTO_EXTS


@dataclass
class Entry:
    display: str
    uid: Optional[int] = None
    star: int = 0
    memo: str = ""


@dataclass
class ParseResult:
    part: Tuple[int, int] = (1, 1)
    entries: List[Entry] = field(default_factory=list)


@dataclass
class Match:
    item: Item
    entry: Entry


_PART_RE = re.compile(r"\[\s*(\d+)\s*/\s*(\d+)\s*\]")
_STAR_RE = re.compile(r"(?:★\s*(\d)|(★+))")
_FILE_RE = re.compile(
    r"[^\s,，、]*?[^\s,，、/\\:*?\"<>|]+\.(?:%s)" % "|".join(
        e.lstrip(".") for e in sorted(PHOTO_EXTS)),
    re.IGNORECASE)


def parse_json_result(text: str) -> ParseResult:
    o = json.loads(text)
    part = tuple(o.get("part", [1, 1]))
    entries = [Entry(display=e.get("d", ""), uid=e.get("u"),
                     star=int(e.get("star", 0) or 0), memo=e.get("memo", "") or "")
               for e in o.get("selected", [])]
    return ParseResult(part=(int(part[0]), int(part[1])), entries=entries)


def parse_text_result(text: str) -> ParseResult:
    """관대 파서: 별점·이모지·구분자 변형 무시, [x/n] 추적, 줄/쉼표 혼용."""
    part = (1, 1)
    m = _PART_RE.search(text)
    if m:
        part = (int(m.group(1)), int(m.group(2)))
    entries = []
    seen = set()
    for line in text.splitlines():
        files = list(_FILE_RE.finditer(line))
        for i, fm in enumerate(files):
            name = unicodedata.normalize("NFC", fm.group(0).strip())
            if name.lower() in seen:
                continue
            seen.add(name.lower())
            star, memo = 0, ""
            # 별점·메모는 한 줄에 파일이 하나일 때만 신뢰 (쉼표 나열 형식엔 없음)
            if len(files) == 1:
                rest = line[fm.end():]
                sm = _STAR_RE.search(rest)
                if sm:
                    star = int(sm.group(1)) if sm.group(1) else len(sm.group(2))
                    rest = rest[sm.end():]
                memo = rest.strip().lstrip("-—:·").strip()
            entries.append(Entry(display=name, star=star, memo=memo))
    return ParseResult(part=part, entries=entries)


def parse_any(text: str) -> ParseResult:
    t = text.strip()
    if t.startswith("{"):
        try:
            return parse_json_result(t)
        except Exception:
            pass
    return parse_text_result(t)


_ILLEGAL_FOLDER = re.compile(r'[\\/:*?"<>|]')


def safe_folder_name(name: str, default: str = "셀렉본") -> str:
    """폴더명에서 Windows 금지문자 제거, 양끝 공백·점 정리. 비면 default."""
    cleaned = _ILLEGAL_FOLDER.sub("", name or "").strip().strip(".").strip()
    return cleaned or default


def _norm(name: str) -> str:
    return unicodedata.normalize("NFC", name).lower()


def _stem(name: str) -> str:
    return os.path.splitext(_norm(name))[0]


class RecoverySession:
    """누적 입력(여러 파트) 병합 + 누락 감지 + 매칭."""

    def __init__(self):
        self.results: List[ParseResult] = []

    def add(self, r: ParseResult):
        self.results.append(r)

    def total_parts(self) -> int:
        return max([r.part[1] for r in self.results] + [1])

    def missing_parts(self) -> List[int]:
        n = self.total_parts()
        have = {r.part[0] for r in self.results}
        return [i for i in range(1, n + 1) if i not in have]

    def all_entries(self) -> List[Entry]:
        out, seen = [], set()
        for r in self.results:
            for e in r.entries:
                key = (e.uid, _norm(e.display))
                if key in seen:
                    continue
                seen.add(key)
                out.append(e)
        return out

    def match(self, mapping: Dict[int, Item]) -> Tuple[List[Match], List[str]]:
        """uid 우선, 없으면 파일명(NFC·대소문자·확장자 유연) 폴백."""
        by_name = {}
        by_stem = {}
        for it in mapping.values():
            by_name.setdefault(_norm(it.display), it)
            by_stem.setdefault(_stem(it.display), it)
        matched, unmatched, used = [], [], set()
        for e in self.all_entries():
            it = None
            if e.uid is not None and e.uid in mapping:
                it = mapping[e.uid]
            else:
                it = by_name.get(_norm(e.display)) or by_stem.get(_stem(e.display))
            if it and it.uid not in used:
                used.add(it.uid)
                matched.append(Match(item=it, entry=e))
            elif it is None:
                unmatched.append(e.display)
        return matched, unmatched


def copy_selected(matched: List[Match], dest_dir: str,
                  save_notes: bool = False) -> Dict:
    """선택분을 단일 폴더로 평탄화 복사(이동 아님). 충돌 시 _2 접미."""
    os.makedirs(dest_dir, exist_ok=True)
    success, failed, dupes = 0, [], 0
    notes = []
    for m in matched:
        src = m.item.path
        base = os.path.basename(src)
        target = os.path.join(dest_dir, base)
        if os.path.exists(target):
            stem, ext = os.path.splitext(base)
            n = 2
            while os.path.exists(os.path.join(dest_dir, "{}_{}{}".format(stem, n, ext))):
                n += 1
            target = os.path.join(dest_dir, "{}_{}{}".format(stem, n, ext))
            dupes += 1
        try:
            shutil.copy2(src, target)
            success += 1
            if m.entry.star or m.entry.memo:
                notes.append("{}\t★{}\t{}".format(m.entry.display, m.entry.star, m.entry.memo))
        except OSError as e:
            failed.append("{} ({})".format(m.item.display, e))
    if save_notes and notes:
        with open(os.path.join(dest_dir, "_셀렉결과.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(notes))
    return {"success": success, "failed": failed, "renamed_dupes": dupes}
