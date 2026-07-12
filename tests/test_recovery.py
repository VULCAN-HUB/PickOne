# -*- coding: utf-8 -*-
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pickone.scanner import Item  # noqa: E402
from pickone.recovery import (  # noqa: E402
    parse_json_result, parse_text_result, RecoverySession, copy_selected,
    safe_folder_name,
)


def items3(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    out = []
    for i, name in enumerate(["IMG_001.jpg", "IMG_002.jpg", "카메라A_IMG_003.jpg"], 1):
        f = tmp_path / name
        f.write_bytes(b"original-%d" % i)
        out.append(Item(i, name, str(f)))
    return out


def test_parse_json():
    j = json.dumps({"app": "pickone", "v": 1, "title": "T", "part": [1, 2],
                    "selected": [{"u": 1, "d": "IMG_001.jpg", "star": 3, "memo": "굿"}]})
    r = parse_json_result(j)
    assert r.part == (1, 2) and r.entries[0].uid == 1 and r.entries[0].star == 3


def test_parse_text_lenient():
    txt = "[1/3] 웨딩 셀렉 결과 (3장)\nIMG_001.jpg ★3 - 보정 부탁\nIMG_002.jpg\n카메라A_IMG_003.jpg ★5"
    r = parse_text_result(txt)
    assert r.part == (1, 3)
    assert [e.display for e in r.entries] == ["IMG_001.jpg", "IMG_002.jpg", "카메라A_IMG_003.jpg"]
    assert r.entries[0].star == 3 and r.entries[0].memo == "보정 부탁"


def test_parse_text_comma_format():
    r = parse_text_result("[2/3] IMG_001.jpg, IMG_002.jpg , IMG_003.jpg")
    assert r.part == (2, 3) and len(r.entries) == 3


def test_session_accumulate_and_missing_parts():
    s = RecoverySession()
    s.add(parse_text_result("[1/3] a.jpg"))
    s.add(parse_text_result("[3/3] b.jpg"))
    assert s.missing_parts() == [2]
    s.add(parse_text_result("[2/3] c.jpg"))
    assert s.missing_parts() == []
    assert len(s.all_entries()) == 3


def test_match_by_uid_and_filename_fallback(tmp_path):
    items = items3(tmp_path)
    mapping = {i.uid: i for i in items}
    s = RecoverySession()
    s.add(parse_json_result(json.dumps({"selected": [{"u": 1, "d": "IMG_001.jpg"}]})))
    s.add(parse_text_result("img_002.JPG"))  # 대소문자 무시 폴백
    matched, unmatched = s.match(mapping)
    assert sorted(m.item.uid for m in matched) == [1, 2] and unmatched == []


def test_copy_flatten_and_report(tmp_path):
    items = items3(tmp_path / "src")
    dest = tmp_path / "dest"
    s = RecoverySession()
    s.add(parse_text_result("IMG_001.jpg\n카메라A_IMG_003.jpg\nNOPE.jpg"))
    matched, unmatched = s.match({i.uid: i for i in items})
    report = copy_selected(matched, str(dest))
    assert report["success"] == 2 and unmatched == ["NOPE.jpg"]
    assert (dest / "IMG_001.jpg").read_bytes() == b"original-1"  # 복사(원본 보존)
    assert (tmp_path / "src" / "IMG_001.jpg").exists()


def test_safe_folder_name_strips_illegal():
    assert safe_folder_name('a/b:c*?"<>|d') == "abcd"
    assert safe_folder_name("  웨딩_셀렉결과 . ") == "웨딩_셀렉결과"


def test_safe_folder_name_empty_default():
    assert safe_folder_name("") == "셀렉본"
    assert safe_folder_name("   ") == "셀렉본"
    assert safe_folder_name("***", default="기본") == "기본"


def test_copy_into_named_subfolder(tmp_path):
    items = items3(tmp_path / "src")
    s = RecoverySession()
    s.add(parse_text_result("IMG_001.jpg"))
    matched, _ = s.match({i.uid: i for i in items})
    dest = os.path.join(str(tmp_path / "loc"), safe_folder_name("내폴더"))
    report = copy_selected(matched, dest)
    assert report["success"] == 1
    assert os.path.isfile(os.path.join(dest, "IMG_001.jpg"))


def test_copy_name_collision(tmp_path):
    f1 = tmp_path / "a" / "X.jpg"; f1.parent.mkdir(); f1.write_bytes(b"1")
    f2 = tmp_path / "b" / "X.jpg"; f2.parent.mkdir(); f2.write_bytes(b"2")
    items = [Item(1, "X.jpg", str(f1)), Item(2, "X.jpg", str(f2))]
    s = RecoverySession()
    s.add(parse_json_result(json.dumps({"selected": [{"u": 1, "d": "X.jpg"}, {"u": 2, "d": "X.jpg"}]})))
    matched, _ = s.match({i.uid: i for i in items})
    dest = tmp_path / "out"
    report = copy_selected(matched, str(dest))
    assert report["success"] == 2
    assert sorted(p.name for p in dest.iterdir()) == ["X.jpg", "X_2.jpg"]
