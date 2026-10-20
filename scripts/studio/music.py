"""Nhạc nền tự tổng hợp (miễn bản quyền, 0 credit) — phương án dự phòng khi chưa có Lyria / file nhạc.

Bám nhịp truyện: mỗi beat có `purpose` → cường độ; nhạc dâng ở leo thang, đập mạnh ở cao trào, rơi về lặng
ở câu hỏi treo với một cú "boom" trầm. Các lớp: drone trầm (D thứ), dây dâng (hợp âm thứ), trống trầm (taiko)
nhanh dần theo cường độ, lớp "không khí" từ nhiễu lọc thấp; reverb bằng tích chập đáp ứng xung tắt dần.
"""

import wave
from pathlib import Path

INTENSITY = {"hook": 0.30, "need": 0.40, "senses": 0.45, "target": 0.50, "escalation": 0.72,
             "climax": 1.00, "cliffhanger": 0.20, "resolution": 0.25}


def _smooth(x, n):
    import numpy as np

    if n <= 1:
        return x
    k = np.ones(n) / n
    return np.convolve(np.pad(x, (n, n), mode="edge"), k, mode="same")[n:-n]


def _tone(f, t, harmonics=6, detune=0.0, rolloff=1.6):
    import numpy as np

    out = np.zeros_like(t)
    for h in range(1, harmonics + 1):
        ph = 2 * np.pi * f * h * (1 + detune) * t + 0.002 * h * np.sin(2 * np.pi * 0.17 * t)
        out += np.sin(ph) / (h ** rolloff)
    return out


def _lowpass_noise(n, sr, cutoff, rng):
    import numpy as np

    x = rng.standard_normal(n)
    a = np.exp(-2 * np.pi * cutoff / sr)  # lọc một cực
    y = np.empty(n)
    acc = 0.0
    for i in range(0, n, 4096):  # vector hóa theo khối bằng lfilter thủ công
        seg = x[i:i + 4096]
        out = np.empty_like(seg)
        for j, v in enumerate(seg):
            acc = a * acc + (1 - a) * v
            out[j] = acc
        y[i:i + 4096] = out
    return y / (np.abs(y).max() + 1e-9)


def _hit(sr, length=1.6, f0=55.0, f1=32.0, decay=5.0):
    """Trống trầm: sine quét tần số xuống + tắt dần."""
    import numpy as np

    t = np.arange(int(sr * length)) / sr
    f = f1 + (f0 - f1) * np.exp(-t * 18)
    ph = 2 * np.pi * np.cumsum(f) / sr
    return np.sin(ph) * np.exp(-t * decay)


def intensity_curve(sections: list, duration: float, sr_ctrl: int = 100):
    """sections: [(t0, t1, purpose)] → cường độ 0–1 theo thời gian (độ phân giải 10 ms), chuyển mượt ~1.2 s."""
    import numpy as np

    n = int(duration * sr_ctrl) + 1
    curve = np.full(n, 0.3)
    for t0, t1, purpose in sections:
        curve[int(t0 * sr_ctrl):int(t1 * sr_ctrl) + 1] = INTENSITY.get(purpose, 0.4)
    return _smooth(curve, int(1.2 * sr_ctrl))


def synth_score(duration: float, sections: list, out_path: Path, sr: int = 48000, seed: int = 7) -> dict:
    import numpy as np

    rng = np.random.default_rng(seed)
    n = int(duration * sr)
    t = np.arange(n) / sr
    ctrl = intensity_curve(sections, duration)
    inten = np.interp(t, np.arange(len(ctrl)) / 100, ctrl)

    # 1. Drone D2 + A2 (quãng 5), hai giọng lệch nhẹ tạo độ dày
    drone = sum(_tone(f, t, 7, d) for f in (73.42, 110.0) for d in (-0.0015, 0.0015)) * 0.18
    drone *= 0.55 + 0.45 * inten
    # 2. Dây dâng: D3 F3 A3 (D thứ), thêm Bb3 khi căng để tạo nghịch tai
    strings = sum(_tone(f, t, 5, d, 2.0) for f in (146.83, 174.61, 220.0) for d in (-0.002, 0.002)) * 0.10
    tension = _tone(233.08, t, 4, 0.001, 2.2) * 0.08 * np.clip((inten - 0.6) / 0.4, 0, 1)
    swell = 0.5 + 0.5 * np.sin(2 * np.pi * t / 7.0 - np.pi / 2)  # thở chậm 7 s
    strings = (strings * swell + tension) * np.clip(inten - 0.25, 0, 1) * 1.6
    # 3. Trống trầm: chỉ khi cường độ ≥ 0.45, nhịp 50 → 115 BPM theo cường độ
    drums = np.zeros(n)
    hit = _hit(sr)
    pos = 0.0
    while pos < duration - 0.5:
        i = int(pos * 100)
        level = ctrl[min(i, len(ctrl) - 1)]
        if level >= 0.45:
            k = int(pos * sr)
            seg = hit[: n - k] * (0.35 + 0.65 * level)
            drums[k:k + len(seg)] += seg
            bpm = 50 + 65 * (level - 0.45) / 0.55
            pos += 60.0 / bpm
        else:
            pos += 0.25
    # 4. Không khí: nhiễu lọc thấp, rất nhỏ
    air = _lowpass_noise(n, sr, 900, rng) * 0.035 * (0.6 + 0.4 * inten)
    mix = drone + strings + drums * 0.55 + air
    # 5. Câu hỏi treo: một cú boom ở đầu đoạn
    for t0, _, purpose in sections:
        if purpose == "cliffhanger":
            k = int(t0 * sr)
            boom = _hit(sr, 4.0, 48.0, 26.0, 1.4) * 0.9
            mix[k:k + len(boom)] += boom[: n - k]
    # Reverb: tích chập với đáp ứng xung tắt dần 2.2 s (FFT)
    ir_t = np.arange(int(sr * 2.2)) / sr
    ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 3.2)
    ir[0] = 1.0
    size = 1 << int(np.ceil(np.log2(n + len(ir))))
    wet = np.fft.irfft(np.fft.rfft(mix, size) * np.fft.rfft(ir / np.abs(ir).sum() * 6, size), size)[:n]
    out = 0.7 * mix + 0.3 * wet
    # Fade đầu/cuối, chuẩn hóa đỉnh −1 dBFS, stereo rộng nhẹ (trễ kênh phải 11 ms)
    fade = np.ones(n)
    fi, fo = int(1.5 * sr), int(2.5 * sr)
    fade[:fi] = np.linspace(0, 1, fi)
    fade[-fo:] = np.linspace(1, 0, fo)
    out *= fade
    out /= np.abs(out).max() + 1e-9
    out *= 10 ** (-1 / 20)
    d = int(0.011 * sr)
    right = np.concatenate([np.zeros(d), out[:-d]])
    stereo = np.stack([out, 0.85 * right + 0.15 * out], axis=1)
    pcm = (stereo * 32767).astype(np.int16)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return {"path": str(out_path), "duration": round(duration, 2), "sections": len(sections)}


def sections_from_timeline(segs: list, project: dict) -> list:
    """[(t0, t1, purpose)] theo beat từ timeline đã tính."""
    from . import beats as bt

    beats = bt.beats_by_id(project)
    out = []
    for s in segs:
        b = beats.get(s["shot"].get("beat"))
        purpose = (b or {}).get("purpose", "need")
        t0, t1 = s["timeline_start"], s["timeline_start"] + s["duration"]
        if out and out[-1][2] == purpose and abs(out[-1][1] - t0) < 0.05:
            out[-1] = (out[-1][0], t1, purpose)
        else:
            out.append((t0, t1, purpose))
    return out
