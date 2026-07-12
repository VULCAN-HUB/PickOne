# -*- coding: utf-8 -*-
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PIL import Image  # noqa: E402

from pickone.scanner import Item  # noqa: E402
from pickone.preview import (  # noqa: E402
    make_webp_datauri, fit_quality, generate_previews,
    fit_to_target, Q_AUTO, Q_FLOOR, Q_CEIL,
)


def make_jpg(p, w=2000, h=1000, exif_orientation=None, gps=False):
    img = Image.new("RGB", (w, h), (200, 50, 0))
    exif = None
    if exif_orientation or gps:
        import piexif
        zeroth = {}
        if exif_orientation:
            zeroth[piexif.ImageIFD.Orientation] = exif_orientation
        gps_ifd = {piexif.GPSIFD.GPSLatitudeRef: b"N"} if gps else {}
        exif = piexif.dump({"0th": zeroth, "GPS": gps_ifd})
    if exif:
        img.save(str(p), "JPEG", exif=exif)
    else:
        img.save(str(p), "JPEG")
    return str(p)


def decode_datauri(uri):
    import base64
    assert uri.startswith("data:image/webp;base64,")
    return Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1])))


def test_resize_to_width(tmp_path):
    f = make_jpg(tmp_path / "a.jpg", 2000, 1000)
    uri = make_webp_datauri(f, 600, 80)
    img = decode_datauri(uri)
    assert img.width == 600 and img.height == 300


def test_no_upscale(tmp_path):
    f = make_jpg(tmp_path / "a.jpg", 400, 200)
    img = decode_datauri(make_webp_datauri(f, 600, 80))
    assert img.width == 400


def test_exif_rotation_applied(tmp_path):
    f = make_jpg(tmp_path / "a.jpg", 2000, 1000, exif_orientation=6)  # 90도 회전
    img = decode_datauri(make_webp_datauri(f, 600, 80))
    assert img.height > img.width  # 세로로 회전됨


def test_metadata_stripped(tmp_path):
    f = make_jpg(tmp_path / "a.jpg", gps=True)
    img = decode_datauri(make_webp_datauri(f, 600, 80))
    assert not img.info.get("exif")


def test_fit_quality_targets_size(tmp_path):
    f = make_jpg(tmp_path / "a.jpg", 3000, 2000)
    q = fit_quality(f, 1000, target_bytes=40_000)
    uri = make_webp_datauri(f, 1000, q)
    raw_len = (len(uri) - 23) * 3 // 4
    assert raw_len <= 60_000  # 목표 근처 이하


def _items_n(tmp_path, n, w=3000, h=2000):
    items = []
    for i in range(1, n + 1):
        f = make_jpg(tmp_path / ("p%03d.jpg" % i), w, h)
        items.append(Item(i, "p%03d.jpg" % i, f))
    return items


def _built_total(items, fit):
    """fit 결과로 실제 인코딩한 data URI 합계 길이(=HTML 본문 근사)."""
    total = 0
    for it in items:
        total += len(make_webp_datauri(it.path, fit["thumb_px"], fit["quality"]))
        total += len(make_webp_datauri(it.path, fit["large_px"], fit["quality"]))
    return total


def test_fit_to_target_large_budget_uses_ceiling(tmp_path):
    items = _items_n(tmp_path, 4)
    fit = fit_to_target(items, target_bytes=50 * 1024 * 1024)  # 넉넉
    assert fit["quality"] == Q_CEIL
    assert (fit["thumb_px"], fit["large_px"]) == (600, 1400)


def test_fit_to_target_small_budget_lowers_quality(tmp_path):
    items = _items_n(tmp_path, 6)
    big = fit_to_target(items, target_bytes=50 * 1024 * 1024)
    small = fit_to_target(items, target_bytes=120_000)  # 빡빡
    assert small["quality"] <= big["quality"]
    assert _built_total(items, small) <= 120_000  # 안전마진 적용 → 목표 이하 보장


def test_fit_to_target_monotonic(tmp_path):
    items = _items_n(tmp_path, 5)
    q_low = fit_to_target(items, 150_000)["quality"]
    q_hi = fit_to_target(items, 1_500_000)["quality"]
    assert q_hi >= q_low


def test_generate_previews_parallel_and_errors(tmp_path):
    good = make_jpg(tmp_path / "g.jpg")
    bad = tmp_path / "b.jpg"
    bad.write_bytes(b"not an image")
    items = [Item(1, "g.jpg", good), Item(2, "b.jpg", str(bad))]
    progress = []
    res = generate_previews(items, thumb_px=600, large_px=1400, quality=70,
                            progress_cb=lambda done, total: progress.append((done, total)))
    assert set(res.thumbs) == {1} and set(res.larges) == {1}
    assert items[1].error  # 손상 파일 사유 기록
    assert progress[-1] == (2, 2)
