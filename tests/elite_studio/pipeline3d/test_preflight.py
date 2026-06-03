import pytest

from skyyrose.elite_studio.pipeline3d.preflight import PreflightError, resolve_source


def test_explicit_image_path_wins(tmp_path):
    img = tmp_path / "explicit.png"
    img.write_bytes(b"x")
    got = resolve_source(sku="br-001", image=img, source_root=tmp_path / "assets")
    assert got == img


def test_explicit_missing_path_raises(tmp_path):
    with pytest.raises(PreflightError):
        resolve_source(sku="br-001", image=tmp_path / "nope.png", source_root=tmp_path)


def test_sku_resolves_front_flatlay(tmp_path):
    folder = tmp_path / "br-001__black-rose-crewneck" / "flatlay"
    folder.mkdir(parents=True)
    (folder / "back.png").write_bytes(b"b")
    front = folder / "front.png"
    front.write_bytes(b"f")
    got = resolve_source(sku="br-001", image=None, source_root=tmp_path)
    assert got == front


def test_sku_without_front_takes_first_sorted(tmp_path):
    folder = tmp_path / "sg-001__sig-tee" / "flatlay"
    folder.mkdir(parents=True)
    (folder / "b.png").write_bytes(b"b")
    (folder / "a.png").write_bytes(b"a")
    got = resolve_source(sku="sg-001", image=None, source_root=tmp_path)
    assert got.name == "a.png"


def test_unknown_sku_raises(tmp_path):
    with pytest.raises(PreflightError):
        resolve_source(sku="zz-999", image=None, source_root=tmp_path)
