import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from studio import media  # noqa: E402
from studio.config import DEFAULT_CONFIG  # noqa: E402


@pytest.fixture
def cfg():
    c = copy.deepcopy(DEFAULT_CONFIG)
    c["output"].update(width=640, height=360)  # render nhanh khi test
    return c


def make_clip(path: Path, seconds=8.0, size="640x360", tone=440, letterbox=0, speech=None):
    """Tạo clip test từ testsrc2 (có chuyển động thật + bộ đếm frame → mỗi frame là duy nhất) + tiếng sine.

    speech=(start, end): chỉ có tiếng trong khoảng này (mô phỏng thoại).
    """
    w, h = map(int, size.split("x"))
    vf = "null"
    if letterbox:
        vf = (f"drawbox=x=0:y=0:w={w}:h={letterbox}:color=black:t=fill,"
              f"drawbox=x=0:y={h - letterbox}:w={w}:h={letterbox}:color=black:t=fill")
    if speech:
        a = f"sine=f={tone}:d={seconds},volume='if(between(t,{speech[0]},{speech[1]}),1,0.003)':eval=frame"
    else:
        a = f"sine=f={tone}:d={seconds}"
    media.run_ffmpeg([
        "-f", "lavfi", "-i", f"testsrc2=s={size}:r=24:d={seconds}",
        "-f", "lavfi", "-i", a,
        "-vf", vf, "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", str(path),
    ])
    return path


@pytest.fixture
def project(tmp_path):
    proj = tmp_path / "proj"
    (proj / "assets" / "clips").mkdir(parents=True)
    manifest = {
        "schema_version": 2, "project_name": "test", "language": "en", "aspect_ratio": "16:9",
        "style_line": "Photorealistic nature documentary", "negative_prompt": "",
        "characters": [{"id": "CHAR_A", "name": "Rex", "identity_line": "an adult T. rex with charcoal scales and closed scaly lips",
                        "reference_images": []}],
        "environments": [], "shots": [],
    }
    (proj / "project_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return proj
