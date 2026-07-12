# -*- coding: utf-8 -*-
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pickone.scanner import Item  # noqa: E402
from pickone.preview import PreviewResult  # noqa: E402
from pickone.builder import build_gallery, estimate_bytes  # noqa: E402

URI = "data:image/webp;base64,UklGRiQAAABXRUJQVlA4IBgAAAAwAQCdASoBAAEAAQAcJaQAA3AA/v3AgAA="


def fake(n):
    items = [Item(i, "img_%03d.jpg" % i, "C:\\src\\img_%03d.jpg" % i) for i in range(1, n + 1)]
    pv = PreviewResult()
    for it in items:
        pv.thumbs[it.uid] = URI
        pv.larges[it.uid] = URI
    return items, pv


def test_build_single_html(tmp_path):
    items, pv = fake(3)
    files = build_gallery(items, pv, title="테스트웨딩", goal=2, notice="안내",
                          out_dir=str(tmp_path))
    assert len(files) == 1
    rec = files[0]
    assert "zip" not in rec
    assert os.path.basename(rec["html"]) == "테스트웨딩.html"
    assert rec["count"] == 3
    html = open(rec["html"], encoding="utf-8").read()
    assert "테스트웨딩" in html and "{{" not in html
    data = json.loads(html.split('id="pickone-data" type="application/json">')[1].split("</script>")[0])
    assert data["goal"] == 2 and len(data["items"]) == 3
    assert data["items"][0]["u"] == 1 and data["items"][0]["t"].startswith("data:image/webp")


def test_build_no_split_even_when_many(tmp_path):
    items, pv = fake(50)
    files = build_gallery(items, pv, title="대량", goal=0, notice="",
                          out_dir=str(tmp_path))
    assert len(files) == 1 and files[0]["count"] == 50


def test_estimate_bytes_positive():
    items, pv = fake(2)
    assert estimate_bytes(items, pv) > 0
