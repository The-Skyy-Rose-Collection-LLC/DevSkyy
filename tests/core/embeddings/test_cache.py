"""EmbeddingCache: content-hash read-through semantics (E-cache).

The headline guarantee: a file OVERWRITTEN at a stable path is NOT served a
stale vector — the cache keys on bytes, not the path."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from skyyrose.core.embeddings.cache import EmbeddingCache
from skyyrose.core.embeddings.errors import EmbedError
from skyyrose.core.embeddings.space import EmbeddingSpace

SPACE_A = EmbeddingSpace("model/a", 4, "v1", revision="r1")
SPACE_B = EmbeddingSpace("model/b", 4, "v1", revision="r1")


class CountingEncoder:
    """Duck-typed encoder: counts computes, returns a per-call-distinct vector."""

    def __init__(self, space=SPACE_A):
        self.space = space
        self.calls = 0

    def embed_image(self, source):
        self.calls += 1
        return np.full(4, float(self.calls), dtype=np.float32)


def _write(path, text="alpha"):
    path.write_text(text)
    return path


def test_same_file_hits_cache(tmp_path):
    f = _write(tmp_path / "a.txt")
    enc = CountingEncoder()
    cache = EmbeddingCache(enc)
    first = cache.embed(f)
    second = cache.embed(f)
    assert enc.calls == 1  # second served from cache
    np.testing.assert_array_equal(first, second)


def test_overwritten_file_is_not_stale(tmp_path):
    # THE E-cache guarantee: same path, changed bytes → recompute.
    f = _write(tmp_path / "shadow.png", "pixels-v1")
    enc = CountingEncoder()
    cache = EmbeddingCache(enc)
    v1 = cache.embed(f)
    _write(f, "pixels-v2-different")  # overwrite at the SAME path
    v2 = cache.embed(f)
    assert enc.calls == 2
    assert not np.array_equal(v1, v2)


def test_distinct_files_distinct_keys(tmp_path):
    a = _write(tmp_path / "a.txt", "one")
    b = _write(tmp_path / "b.txt", "two")
    enc = CountingEncoder()
    cache = EmbeddingCache(enc)
    cache.embed(a)
    cache.embed(b)
    assert enc.calls == 2


def test_disk_persistence_across_instances(tmp_path):
    f = _write(tmp_path / "a.txt")
    disk = tmp_path / "cache"
    enc1 = CountingEncoder()
    EmbeddingCache(enc1, disk_dir=disk).embed(f)
    assert enc1.calls == 1
    # New cache + new encoder, same disk dir → served from disk, no recompute.
    enc2 = CountingEncoder()
    EmbeddingCache(enc2, disk_dir=disk).embed(f)
    assert enc2.calls == 0


def test_corrupt_disk_entry_is_a_miss(tmp_path):
    f = _write(tmp_path / "a.txt")
    disk = tmp_path / "cache"
    enc = CountingEncoder()
    cache = EmbeddingCache(enc, disk_dir=disk)
    # Forge a corrupt entry at the exact key path.
    key = cache._key(cache._hash_bytes(f.read_bytes()))
    cache._disk_path(key).write_bytes(b"not a valid npy file")
    out = cache.embed(f)  # must not raise
    assert enc.calls == 1
    assert out.shape == (4,)


def test_different_space_no_collision(tmp_path):
    f = _write(tmp_path / "a.txt")
    disk = tmp_path / "cache"
    EmbeddingCache(CountingEncoder(SPACE_A), disk_dir=disk).embed(f)
    enc_b = CountingEncoder(SPACE_B)
    EmbeddingCache(enc_b, disk_dir=disk).embed(f)
    assert enc_b.calls == 1  # different space.key() → no false hit on A's entry


def test_pil_image_not_cached(tmp_path):
    enc = CountingEncoder()
    cache = EmbeddingCache(enc)
    img = Image.new("RGB", (4, 4))
    cache.embed(img)
    cache.embed(img)
    assert enc.calls == 2  # no stable identity → encode each time


def test_missing_file_raises(tmp_path):
    enc = CountingEncoder()
    cache = EmbeddingCache(enc)
    with pytest.raises(EmbedError):
        cache.embed(tmp_path / "nope.txt")
