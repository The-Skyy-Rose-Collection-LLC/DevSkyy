"""Stage F shadows must fail closed on a PIL/IO error, not silently return the
un-shadowed composite labeled as a shadow path. The legitimate skip-shadow
early-return (subject fills >85% of frame, no ground plane) is unrelated and
must be preserved unchanged.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from skyyrose.elite_studio.agents.compositor.stage_f_shadows import (
    ShadowStageError,
    generate_shadows,
)

pytestmark = pytest.mark.unit


def test_skip_shadow_when_subject_fills_frame(tmp_path: Path) -> None:
    src = tmp_path / "composite.png"
    Image.new("RGBA", (100, 100), (0, 0, 0, 255)).save(src)  # fully opaque
    assert generate_shadows(str(src), "br-001", str(tmp_path)) == str(src)


def test_shadow_written_when_ground_plane_visible(tmp_path: Path) -> None:
    composite = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    composite.paste(Image.new("RGBA", (50, 50), (200, 100, 100, 255)), (75, 75))
    src = tmp_path / "composite.png"
    composite.save(src)
    result = generate_shadows(str(src), "br-001", str(tmp_path))
    assert "shadow" in result and Path(result).exists() and result != str(src)


def test_fail_closed_on_pil_error(tmp_path: Path) -> None:
    src = tmp_path / "composite.png"
    Image.new("RGBA", (100, 100), (0, 0, 0, 10)).save(src)  # sparse alpha -> shadow branch
    with patch(
        "skyyrose.elite_studio.agents.compositor.stage_f_shadows.Image.open",
        side_effect=OSError("disk full"),
    ):
        with pytest.raises(ShadowStageError, match="disk full"):
            generate_shadows(str(src), "br-001", str(tmp_path))
