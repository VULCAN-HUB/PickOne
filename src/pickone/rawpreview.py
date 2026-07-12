# -*- coding: utf-8 -*-
"""RAW 임베디드 프리뷰 추출 — 외부 의존성 없이 컨테이너에서 JPEG을 직접 꺼낸다.

- CR3 (ISO-BMFF): PRVW 박스 내 풀사이즈 JPEG.
- TIFF 기반 RAW(NEF/DNG/ARW/CR2 등): Pillow가 IFD를 읽을 수 있으면 그대로,
  아니면 파일 내 최대 JPEG 스트림 스캔 폴백.
"""
import io
import struct

from PIL import Image


def _cr3_prvw_jpeg(data: bytes):
    idx = data.find(b"PRVW")
    if idx < 4:
        return None
    box_start = idx - 4
    (box_size,) = struct.unpack(">I", data[box_start:box_start + 4])
    end = min(box_start + box_size, len(data))
    soi = data.find(b"\xff\xd8\xff", idx, end)
    if soi < 0:
        return None
    eoi = data.rfind(b"\xff\xd9", soi, end)
    return data[soi:eoi + 2] if eoi > soi else data[soi:end]


def _largest_jpeg_stream(data: bytes):
    """파일 전체에서 가장 큰 SOI..EOI 구간(임베디드 프리뷰일 확률 최대)."""
    best = None
    pos = 0
    while True:
        soi = data.find(b"\xff\xd8\xff", pos)
        if soi < 0:
            break
        eoi = data.find(b"\xff\xd9", soi + 3)
        if eoi < 0:
            break
        chunk = data[soi:eoi + 2]
        if best is None or len(chunk) > len(best):
            best = chunk
        pos = eoi + 2
    return best


def extract_raw_preview(path: str) -> Image.Image:
    """RAW 파일에서 임베디드 JPEG 프리뷰를 PIL 이미지로. 실패 시 예외."""
    with open(path, "rb") as f:
        data = f.read()
    jpeg = None
    if b"ftypcrx" in data[:32]:  # CR3
        jpeg = _cr3_prvw_jpeg(data)
    if jpeg is None:
        jpeg = _largest_jpeg_stream(data)
    if not jpeg or len(jpeg) < 10_000:  # 너무 작으면 썸네일 수준 — 신뢰 불가
        raise ValueError("임베디드 프리뷰 없음")
    img = Image.open(io.BytesIO(jpeg))
    img.load()
    return img
