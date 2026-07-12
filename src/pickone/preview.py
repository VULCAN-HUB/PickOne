# -*- coding: utf-8 -*-
"""WebP 2단 프리뷰 생성 — EXIF 회전 적용, GPS·메타 제거, 품질 자동 역산, 병렬."""
import base64
import io
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from PIL import Image, ImageOps

from .scanner import Item, RAW_EXTS

Q_AUTO = 80      # 자동 모드 시각적 무손실 품질 (용량 제한 없음)
Q_FLOOR = 10     # 목표 모드 최저 품질 (이 밑은 해상도 강등)
Q_CEIL = 95      # 목표 모드 최고 품질
SAMPLE_MAX = 12  # 전역 품질 추정 표본 수
SAFETY = 0.93    # 목표 용량 안전마진(표본 추정 오차로 실제가 목표를 넘지 않도록)
TEMPLATE_OVERHEAD = 30_000  # 템플릿 고정분(builder.estimate_bytes와 일치)
# 해상도 강등 단계 (thumb_px, large_px): 앞에서부터 시도, 뒤로 갈수록 작아짐
RES_STEPS = [(600, 1400), (600, 1000), (500, 800), (400, 600), (300, 400)]

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_OK = True
except Exception:
    HEIC_OK = False


@dataclass
class PreviewResult:
    thumbs: Dict[int, str] = field(default_factory=dict)   # uid -> data URI (600px)
    larges: Dict[int, str] = field(default_factory=dict)   # uid -> data URI (1400px)
    exif_dts: Dict[int, str] = field(default_factory=dict)  # uid -> "YYYY:MM:DD HH:MM:SS"


def _load_image(path: str) -> Image.Image:
    """이미지 로드. RAW는 임베디드 JPEG 프리뷰 추출(rawpreview), 그 외 Pillow 직접."""
    ext = os.path.splitext(path)[1].lower()
    if ext in RAW_EXTS:
        try:
            img = Image.open(path)
            img.load()
        except Exception:
            from .rawpreview import extract_raw_preview
            img = extract_raw_preview(path)
    else:
        img = Image.open(path)
    img = ImageOps.exif_transpose(img)  # EXIF 회전 적용
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    return img


def _exif_datetime(path: str) -> Optional[str]:
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            return exif.get(36867) or exif.get(306)  # DateTimeOriginal / DateTime
    except Exception:
        return None


def _encode_webp(img: Image.Image, width: int, quality: int) -> bytes:
    if img.width > width:
        h = max(1, round(img.height * width / img.width))
        img = img.resize((width, h), Image.LANCZOS)
    buf = io.BytesIO()
    # exif/메타 미전달 → GPS 포함 메타 전부 제거됨
    img.save(buf, "WEBP", quality=quality, method=6)
    return buf.getvalue()


def make_webp_datauri(path: str, width: int, quality: int) -> str:
    data = _encode_webp(_load_image(path), width, quality)
    return "data:image/webp;base64," + base64.b64encode(data).decode("ascii")


def fit_quality(path: str, width: int, target_bytes: int, lo: int = 30, hi: int = 85) -> int:
    """단일 샘플 이미지 기준, 목표 바이트 이하가 되는 최대 품질(q)을 이진탐색."""
    img = _load_image(path)
    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        size = len(_encode_webp(img, width, mid))
        if size <= target_bytes:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def _datauri_len(img: Image.Image, width: int, quality: int) -> int:
    """인코딩 후 data URI 문자열 길이(HTML에 실제로 들어가는 크기)."""
    raw = _encode_webp(img, width, quality)
    return 23 + ((len(raw) + 2) // 3) * 4  # "data:image/webp;base64," + base64 길이


def _sample(items: List[Item], k: int) -> List[Item]:
    n = len(items)
    if n <= k:
        return list(items)
    step = n / k
    return [items[int(i * step)] for i in range(k)]


def fit_to_target(items: List[Item], target_bytes: int,
                  sample_max: int = SAMPLE_MAX) -> Dict[str, int]:
    """전체 HTML 본문이 target_bytes 이하가 되는 {quality, thumb_px, large_px}를 찾는다.
    1순위 품질 이진탐색(Q_FLOOR~Q_CEIL), 최저 품질로도 초과면 해상도를 단계적으로 강등.
    어떤 경우에도 목표를 넘기지 않도록 best-effort로 가장 작은 조합까지 내려간다."""
    sample_items = _sample(items, sample_max)
    imgs = []
    for it in sample_items:
        try:
            imgs.append(_load_image(it.path))
        except Exception:
            pass
    if not imgs:
        return {"quality": Q_AUTO, "thumb_px": 600, "large_px": 1400}
    count = len(items)
    budget = int(target_bytes * SAFETY)  # 추정 오차 흡수용 안전마진 적용

    def est(thumb_px: int, large_px: int, q: int) -> float:
        tot = 0
        for img in imgs:
            tot += _datauri_len(img, thumb_px, q) + _datauri_len(img, large_px, q)
        return tot / len(imgs) * count + TEMPLATE_OVERHEAD

    for idx, (thumb_px, large_px) in enumerate(RES_STEPS):
        last = idx == len(RES_STEPS) - 1
        if not last and est(thumb_px, large_px, Q_FLOOR) > budget:
            continue  # 이 해상도는 최저 품질로도 초과 → 더 작은 해상도로
        lo, hi, best = Q_FLOOR, Q_CEIL, Q_FLOOR
        while lo <= hi:
            mid = (lo + hi) // 2
            if est(thumb_px, large_px, mid) <= budget:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return {"quality": best, "thumb_px": thumb_px, "large_px": large_px}

    t, l = RES_STEPS[-1]
    return {"quality": Q_FLOOR, "thumb_px": t, "large_px": l}


def generate_previews(items: List[Item], thumb_px: int = 600, large_px: int = 1400,
                      quality: int = 70, large_quality: Optional[int] = None,
                      progress_cb: Optional[Callable[[int, int], None]] = None,
                      workers: int = 4) -> PreviewResult:
    res = PreviewResult()
    lq = large_quality if large_quality is not None else quality
    total = len(items)

    def work(item: Item):
        ext = os.path.splitext(item.path)[1].lower()
        if ext in (".heic", ".heif") and not HEIC_OK:
            raise RuntimeError("HEIC 모듈 없음 — JPEG으로 변환 후 사용하세요")
        img = _load_image(item.path)
        thumb = _encode_webp(img, thumb_px, quality)
        large = _encode_webp(img, large_px, lq)
        dt = _exif_datetime(item.path)
        return item.uid, thumb, large, dt

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(work, it): it for it in items}
        for fut in as_completed(futs):
            item = futs[fut]
            try:
                uid, thumb, large, dt = fut.result()
                res.thumbs[uid] = "data:image/webp;base64," + base64.b64encode(thumb).decode("ascii")
                res.larges[uid] = "data:image/webp;base64," + base64.b64encode(large).decode("ascii")
                if dt:
                    res.exif_dts[uid] = str(dt)
                    item.exif_dt = str(dt)
            except Exception as e:
                kind = "RAW 임베디드 프리뷰 추출 실패" if os.path.splitext(item.path)[1].lower() in RAW_EXTS else str(e)
                item.error = kind
            done += 1
            if progress_cb:
                progress_cb(done, total)
    return res
