# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pickone.scanner import scan, PHOTO_EXTS  # noqa: E402


def make(p, name):
    f = p / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(b"x")
    return f


def test_recursive_flatten_and_photo_filter(tmp_path):
    make(tmp_path, "a.jpg")
    make(tmp_path, "sub/b.png")
    make(tmp_path, "sub/deep/c.heic")
    make(tmp_path, "movie.mp4")          # 영상 제외
    make(tmp_path, "notes.txt")          # 비이미지 제외
    items = scan([str(tmp_path)])
    names = [i.display for i in items]
    assert names == ["a.jpg", "b.png", "c.heic"]  # 파일명순 정렬


def test_collision_gets_folder_prefix(tmp_path):
    make(tmp_path, "카메라A/IMG_001.jpg")
    make(tmp_path, "카메라B/IMG_001.jpg")
    items = scan([str(tmp_path)])
    names = sorted(i.display for i in items)
    assert names == ["카메라A_IMG_001.jpg", "카메라B_IMG_001.jpg"]


def test_double_collision_gets_numeric_suffix(tmp_path):
    make(tmp_path, "A/IMG_001.jpg")
    f1 = make(tmp_path, "B/IMG_001.jpg")
    # 같은 폴더명 접두까지 겹치는 경우를 흉내내기 위해 동일 구조 두 루트 전달
    items = scan([str(tmp_path / "A"), str(tmp_path / "B"), str(f1.parent)])
    names = [i.display for i in items]
    assert len(names) == len(set(names))  # 어떤 경우에도 표시명 고유


def test_uid_sequential_and_paths_absolute(tmp_path):
    make(tmp_path, "a.jpg")
    make(tmp_path, "b.jpg")
    items = scan([str(tmp_path)])
    assert [i.uid for i in items] == [1, 2]
    assert all(os.path.isabs(i.path) for i in items)


def test_single_file_input(tmp_path):
    f = make(tmp_path, "one.jpg")
    items = scan([str(f)])
    assert len(items) == 1 and items[0].display == "one.jpg"


def test_raw_extensions_included():
    for e in (".cr2", ".cr3", ".nef", ".arw", ".dng"):
        assert e in PHOTO_EXTS
