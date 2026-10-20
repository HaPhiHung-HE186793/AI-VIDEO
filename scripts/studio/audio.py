"""Audio: ước lượng vùng thoại trong clip Veo và tổng hợp lời dẫn (TTS) bằng Gemini API.

Lời dẫn/thoại do Veo sinh ra đổi giọng giữa các clip, nên với phim nhiều shot nên dùng
`voiceover_external`: mỗi shot có 1 file WAV TTS cùng một giọng, và dựng hình theo lời dẫn.
"""

import os
import wave
from pathlib import Path

from . import media


def speech_window(path: Path, win_sec: float = 0.05) -> dict:
    """Ước lượng [start, end] của vùng âm thanh nổi bật (thoại) bằng ngưỡng thích ứng theo nền ồn.

    Đây là ƯỚC LƯỢNG: clip có SFX lớn (gầm, nổ) sẽ bị tính là "thoại". Khi cần chính xác,
    đặt `edit_in` / `edit_out` trong manifest hoặc dùng lời dẫn ngoài.
    """
    import numpy as np

    pcm = media.read_pcm(path, sr=16000)
    dur = len(pcm) / 16000.0
    if len(pcm) < 1600:
        return {"start": 0.0, "end": dur, "duration": dur, "reliable": False}
    hop = int(16000 * win_sec)
    rms = np.array([np.sqrt(np.mean(pcm[i:i + hop] ** 2)) + 1e-9 for i in range(0, len(pcm) - hop, hop)])
    db = 20 * np.log10(rms)
    floor = float(np.percentile(db, 15))
    thr = max(floor + 12.0, -45.0)
    active = db >= thr
    # Yêu cầu ≥3 cửa sổ liên tiếp để bỏ tiếng click lẻ.
    runs = np.convolve(active.astype(int), np.ones(3, dtype=int), mode="same") >= 3
    idx = np.flatnonzero(runs)
    if idx.size == 0:
        return {"start": 0.0, "end": dur, "duration": dur, "reliable": False}
    start = float(max(0.0, (idx[0] - 1) * win_sec))
    end = float(min(dur, (idx[-1] + 2) * win_sec))
    return {"start": round(start, 2), "end": round(end, 2), "duration": round(dur, 2),
            "reliable": float(np.max(db)) - floor >= 15.0}


def voice_profile(path: Path, sr: int = 16000) -> dict:
    """Đặc trưng giọng thô: cao độ (F0) trung vị & độ dao động, đường bao phổ 24 dải trên các frame có tiếng.

    Dùng để SO SÁNH 2 clip cùng một giọng gắn trên Flow. Nhạc/SFX lớn làm sai lệch số đo — clip thử nên yên tĩnh.
    """
    import numpy as np

    pcm = media.read_pcm(path, sr=sr)  # ffmpeg đọc được cả WAV lẫn MP4
    frame, hop = int(0.04 * sr), int(0.02 * sr)
    if len(pcm) < frame * 10:
        return {"voiced_sec": 0.0}
    frames = np.lib.stride_tricks.sliding_window_view(pcm, frame)[::hop]
    energy = np.sqrt((frames ** 2).mean(axis=1)) + 1e-9
    voiced = frames[20 * np.log10(energy) > np.percentile(20 * np.log10(energy), 60)]
    window = np.hanning(frame)
    lo, hi = int(sr / 400), int(sr / 70)  # F0 trong khoảng 70–400 Hz
    unbias = frame - np.arange(frame)     # tự tương quan không lệch: tránh ưu tiên chu kỳ ngắn
    f0s, specs = [], []
    freqs = np.fft.rfftfreq(frame, 1 / sr)
    # 16 dải log từ 200 Hz → 8 kHz; mỗi dải đủ rộng để chứa ≥ 2 bin FFT (bin = 25 Hz)
    band = np.digitize(freqs, np.geomspace(200, sr / 2, 17)) - 1
    valid = (band >= 0) & (band < 16)
    for f in voiced:
        x = f - f.mean()
        ac = np.correlate(x, x, mode="full")[frame - 1:] / unbias
        if ac[0] <= 0:
            continue
        r = ac / ac[0]
        seg = r[lo:hi]
        best = float(seg.max())
        if best > 0.5:  # chỉ lấy frame có cao độ rõ (nguyên âm)
            # Chống lỗi quãng tám: lấy đỉnh cục bộ có chu kỳ NGẮN NHẤT đạt ≥ 90% đỉnh cao nhất.
            peaks = np.flatnonzero((seg[1:-1] >= seg[:-2]) & (seg[1:-1] >= seg[2:]) & (seg[1:-1] >= 0.9 * best)) + 1
            lag = lo + int(peaks[0] if peaks.size else np.argmax(seg))
            f0s.append(sr / lag)
        mag = np.abs(np.fft.rfft(x * window))
        sums = np.bincount(band[valid], weights=mag[valid], minlength=16)
        counts = np.bincount(band[valid], minlength=16)
        specs.append(np.log(sums / np.maximum(counts, 1) + 1e-9))
    if len(f0s) < 10:
        return {"voiced_sec": round(len(voiced) * 0.02, 2)}
    env = np.mean(specs, axis=0)
    return {"voiced_sec": round(len(voiced) * 0.02, 2), "f0_median_hz": round(float(np.median(f0s)), 1),
            "f0_iqr_hz": round(float(np.subtract(*np.percentile(f0s, [75, 25]))), 1),
            "spectral_envelope": (env - env.mean()).tolist()}


def compare_voice_profiles(a: dict, b: dict) -> dict:
    """So 2 profile: chênh cao độ (%) + độ giống đường bao phổ (cosine). Ngưỡng là ước lượng."""
    import numpy as np

    if "f0_median_hz" not in a or "f0_median_hz" not in b:
        return {"verdict": "không đủ dữ liệu", "note": "Clip quá ít tiếng nói rõ."}
    f0_diff = abs(a["f0_median_hz"] - b["f0_median_hz"]) / min(a["f0_median_hz"], b["f0_median_hz"]) * 100
    ea, eb = np.array(a["spectral_envelope"]), np.array(b["spectral_envelope"])
    timbre = float(ea @ eb / (np.linalg.norm(ea) * np.linalg.norm(eb) + 1e-9))
    if f0_diff <= 8 and timbre >= 0.9:
        verdict = "rất có thể cùng giọng"
    elif f0_diff <= 15 and timbre >= 0.8:
        verdict = "gần giống — nghe lại bằng tai"
    else:
        verdict = "khác giọng rõ"
    return {"f0_diff_percent": round(f0_diff, 1), "timbre_similarity": round(timbre, 3), "verdict": verdict}


def fit_narration(src: Path, dst: Path, max_sec: float, max_pause: float = 0.3, max_tempo: float = 1.25) -> dict:
    """Siết nhịp lời dẫn như dựng phim viên: cắt lặng đầu/cuối, rút khoảng lặng dài về `max_pause`,
    rồi tăng tốc (giữ cao độ) nếu vẫn dài hơn `max_sec`. Trả về thông tin trước/sau."""
    import numpy as np

    with wave.open(str(src), "rb") as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32)
    before = len(x) / sr
    hop = int(sr * 0.01)
    rms = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) + 1e-9 for i in range(0, len(x), hop)])
    db = 20 * np.log10(rms / 32768.0)
    # "Lặng" = thấp hơn mức nói thường (p90) 25 dB: bắt được cả khoảng nghỉ có tiếng thở / nền phòng của TTS.
    silent = db < max(float(np.percentile(db, 90)) - 25, -60)
    voiced = np.flatnonzero(~silent)
    if voiced.size == 0:
        return {"before_sec": before, "after_sec": before, "tempo": 1.0}
    keep = np.zeros(len(silent), dtype=bool)
    keep[max(0, voiced[0] - 5): voiced[-1] + 8] = True          # giữ 50 ms trước / 80 ms sau
    i, max_frames = voiced[0], int(max_pause / 0.01)
    while i < voiced[-1]:                                         # rút khoảng lặng giữa câu
        if silent[i]:
            j = i
            while j < len(silent) and silent[j]:
                j += 1
            if j - i > max_frames:
                cut_from = i + max_frames // 2
                keep[cut_from: j - max_frames // 2] = False
            i = j
        else:
            i += 1
    mask = np.repeat(keep, hop)[: len(x)]
    y = x[mask].astype(np.int16)
    tmp = Path(dst).with_suffix(".tight.wav")
    _write_wav(tmp, y.tobytes(), sr)
    tight = len(y) / sr
    tempo = min(max_tempo, tight / max_sec) if tight > max_sec else 1.0
    if tempo > 1.0:
        media.run_ffmpeg(["-i", str(tmp), "-af", f"atempo={tempo:.4f}", "-ar", str(sr), "-ac", "1", str(dst)])
        tmp.unlink()
    else:
        tmp.replace(dst)
    return {"before_sec": round(before, 2), "after_sec": round(wav_duration(Path(dst)), 2), "tempo": round(tempo, 3)}


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def _write_wav(path: Path, pcm_bytes: bytes, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm_bytes)


def tts_available() -> tuple:
    try:
        from google import genai  # noqa: F401
    except ImportError:
        return False, "chưa cài google-genai (pip install google-genai)"
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        return False, "chưa đặt biến môi trường GEMINI_API_KEY"
    return True, ""


def _retry_after(err) -> float:
    """Số giây cần chờ từ lỗi 429 của Gemini API (mặc định 30s)."""
    import re

    m = re.search(r"'retryDelay': '(\d+)s'", str(err)) or re.search(r"retry in ([\d.]+)s", str(err))
    return float(m.group(1)) + 2 if m else 30.0


class QuotaExhausted(Exception):
    """Hết hạn mức miễn phí dài hạn (vd. theo ngày) — dừng lại, phần đã tạo được giữ; chạy lại khi hạn mức đặt lại."""


def tts_prompt(text: str, direction: str = "") -> str:
    """Chỉ đạo giọng theo mẫu của Gemini TTS: "Say <cách đọc>: <câu>".

    Viết chỉ đạo thành câu mệnh lệnh ngắn bắt đầu bằng "Say"; dạng câu dài kèm xuống dòng dễ bị đọc thành lời.
    """
    direction = (direction or "").strip().rstrip(":").strip()
    return f"{direction}: {text}" if direction else text


def text_hash(text: str, voice: str, direction: str, model: str) -> str:
    """Dấu vân tay của 1 câu lời dẫn: đổi chữ / giọng / chỉ đạo / model → phải đọc lại; không đổi → dùng lại file (tiết kiệm hạn mức)."""
    import hashlib

    return hashlib.sha256("|".join([text.strip(), voice or "", direction or "", model or ""]).encode("utf-8")).hexdigest()[:16]


def expected_speech_sec(text: str, words_per_sec: float = 2.3) -> float:
    return len(text.split()) / words_per_sec


def transcribe(path: Path, cfg: dict) -> str:
    """Chép lại lời trong file âm thanh (kiểm tra TTS đọc đúng kịch bản). Trả về "" nếu không gọi được."""
    from google import genai
    from google.genai import types

    client = genai.Client()
    mime = "audio/wav" if Path(path).suffix.lower() == ".wav" else "audio/mp4"
    try:
        r = client.models.generate_content(model=cfg["models"]["gemini_transcribe"],
                                           contents=[types.Part.from_bytes(data=Path(path).read_bytes(), mime_type=mime)])
    except Exception:  # noqa: BLE001 — kiểm tra phụ, không chặn quy trình
        return ""
    texts = []
    for part in r.candidates[0].content.parts:
        tr = getattr(part, "audio_transcription", None)
        texts.append(getattr(tr, "text", None) or part.text or "")
    return " ".join(x for x in texts if x).strip()


_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def _number_words(n: int) -> list:
    """Số → từ tiếng Anh (0–999 999), để "66" khớp "sixty-six" khi so bản chép lời."""
    if n < 20:
        return [_ONES[n]]
    if n < 100:
        return [_TENS[n // 10]] + ([_ONES[n % 10]] if n % 10 else [])
    if n < 1000:
        return [_ONES[n // 100], "hundred"] + (_number_words(n % 100) if n % 100 else [])
    if n < 1_000_000:
        return _number_words(n // 1000) + ["thousand"] + (_number_words(n % 1000) if n % 1000 else [])
    return [str(n)]


def words_match(expected: str, heard: str) -> float:
    """Tỷ lệ từ của kịch bản xuất hiện đúng thứ tự trong bản chép lời (0–1)."""
    import difflib
    import re

    def norm(s):
        words = []
        for w in re.findall(r"[\w']+", s.lower().replace("-", " ")):
            words += _number_words(int(w)) if w.isdigit() else [w]
        return words

    a, b = norm(expected), norm(heard)
    if not a:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def synthesize(text: str, out_wav: Path, cfg: dict, voice: str = None, direction: str = "", max_tries: int = 6,
               model: str = None) -> float:
    """Gọi Gemini TTS, ghi WAV mono PCM16, trả về thời lượng (giây). Tự chờ khi chạm hạn mức (429)."""
    import time

    from google import genai
    from google.genai import errors, types

    client = genai.Client()
    model = model or cfg["models"]["gemini_tts"]
    config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice or cfg["tts"]["voice"])
            )
        ),
    )
    for attempt in range(max_tries):
        try:
            resp = client.models.generate_content(model=model,
                                                  contents=tts_prompt(text, direction), config=config)
            break
        except errors.ClientError as e:
            if getattr(e, "code", None) != 429 or attempt == max_tries - 1:
                raise
            wait = _retry_after(e)
            if wait > 120:
                raise QuotaExhausted(f"Model {model} hết hạn mức (chờ {wait / 3600:.1f} giờ). "
                                     "Phần đã tạo được giữ — chạy lại `voiceover` sau khi hạn mức miễn phí đặt lại "
                                     "(dự án không dùng dịch vụ trả phí).") from e
            time.sleep(wait)
    data = resp.candidates[0].content.parts[0].inline_data.data
    _write_wav(Path(out_wav), data, cfg["tts"]["sample_rate"])
    return wav_duration(Path(out_wav))
