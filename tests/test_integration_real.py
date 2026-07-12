# -*- coding: utf-8 -*-
"""실데이터(CR3) 패키징 → 결과 json → 회수 왕복 통합 테스트."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pickone.scanner import scan  # noqa: E402
from pickone.preview import generate_previews  # noqa: E402
from pickone.builder import build_gallery  # noqa: E402
from pickone.recovery import RecoverySession, parse_json_result, copy_selected  # noqa: E402

REAL = r"C:\Users\princ\Desktop\106CANON (1)"

pytestmark = pytest.mark.skipif(not os.path.isdir(REAL), reason="실데이터 폴더 없음")


def test_roundtrip_cr3(tmp_path):
    items = scan([REAL])[:5]  # CR3 5장
    assert items, "CR3 수집 실패"
    pv = generate_previews(items, quality=70)
    errs = [i for i in items if i.error]
    assert not errs, "프리뷰 실패: %s" % [(i.display, i.error) for i in errs]

    files = build_gallery(items, pv, title="실측테스트", goal=3, notice="",
                          out_dir=str(tmp_path))
    assert len(files) == 1 and os.path.getsize(files[0]["html"]) > 100_000

    # 클라이언트가 2장 선택했다고 가정한 결과 json
    result = json.dumps({"app": "pickone", "v": 1, "title": "실측테스트", "part": [1, 1],
                         "selected": [{"u": items[0].uid, "d": items[0].display, "star": 5, "memo": "베스트"},
                                      {"u": items[2].uid, "d": items[2].display, "star": 0, "memo": ""}]})
    s = RecoverySession()
    s.add(parse_json_result(result))
    matched, unmatched = s.match({i.uid: i for i in items})
    assert len(matched) == 2 and not unmatched

    dest = tmp_path / "selected"
    report = copy_selected(matched, str(dest), save_notes=True)
    assert report["success"] == 2
    copied = sorted(p.name for p in dest.iterdir())
    assert items[0].display in copied and (dest / "_셀렉결과.txt").exists()
    # 원본과 동일 바이트(복사 검증)
    assert (dest / items[0].display).stat().st_size == os.path.getsize(items[0].path)
