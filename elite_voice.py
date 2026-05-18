"""
elite_voice.py — Advanced voice pipeline, buffering
====================================================
Streaming optimization, audio quality metrics, adaptive VAD, TTS text cleaning.
"""

import re
from collections import deque
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import numpy as np


def _clean_text_for_tts(text: str) -> str:
    """Strip markdown and code formatting so it reads naturally when spoken aloud.

    Removes headers, bold/italic markers, inline code, code fences, URLs, and
    list markers that would be read literally by TTS engines.
    """
    # Code fences — omit the fence markers; spoken content reads fine without them
    text = re.sub(r"```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"```", "", text)
    # Inline code — unwrap backticks
    text = re.sub(r"`([^`\n]+)`", r"\1", text)
    # Markdown headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Bold / italic (*** ** * ___ __ _)
    text = re.sub(r"\*{1,3}([^*\n]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}([^_\n]+)_{1,3}", r"\1", text)
    # Ordered and unordered list markers
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Bare URLs — replace with the word "link"
    text = re.sub(r"https?://\S+", "link", text)
    # Horizontal rules
    text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Collapse runs of blank lines and trailing spaces
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


@dataclass
class AudioMetrics:
    """Audio stream quality metrics."""
    rms_level: float
    peak: float
    noise_floor: float
    signal_to_noise: float
    clipping_detected: bool

class AudioBuffer:
    """Smart ring buffer for streaming audio with backpressure."""

    def __init__(self, capacity_frames: int = 4800):
        self.buffer = deque(maxlen=capacity_frames)
        self.capacity = capacity_frames
        self.overflows = 0
        self.underflows = 0

    def put(self, audio_chunk: np.ndarray) -> bool:
        """Add audio chunk. Returns False if buffer full (backpressure)."""
        if len(self.buffer) >= self.capacity * 0.9:  # 90% full triggers backpressure
            self.overflows += 1
            return False

        self.buffer.extend(audio_chunk)
        return True

    def get(self, frame_count: int) -> np.ndarray:
        """Extract audio chunk."""
        frames = []
        for _ in range(min(frame_count, len(self.buffer))):
            if self.buffer:
                frames.append(self.buffer.popleft())

        if len(frames) < frame_count:
            self.underflows += 1

        return np.array(frames) if frames else np.array([])

    def available(self) -> int:
        """Frames available in buffer."""
        return len(self.buffer)

    def stats(self) -> dict:
        return {
            "available": len(self.buffer),
            "capacity": self.capacity,
            "overflows": self.overflows,
            "underflows": self.underflows,
            "fill_percent": round(len(self.buffer) / self.capacity * 100, 1),
        }

class VoiceMetricsAnalyzer:
    """Analyze audio stream quality in real-time."""

    def __init__(self, sr: int = 16000, window_frames: int = 512):
        self.sr = sr
        self.window_frames = window_frames
        self.recent_frames = deque(maxlen=window_frames)
        self.noise_baseline: float = 50.0  # Baseline noise floor estimate

    def analyze(self, audio_chunk: np.ndarray) -> AudioMetrics:
        """Analyze audio chunk for quality metrics."""
        if len(audio_chunk) == 0:
            return AudioMetrics(
                rms_level=0.0,
                peak=0.0,
                noise_floor=self.noise_baseline,
                signal_to_noise=0.0,
                clipping_detected=False,
            )

        self.recent_frames.extend(audio_chunk)
        window = np.array(list(self.recent_frames))

        # RMS level (loudness)
        rms = np.sqrt(np.mean(window ** 2))

        # Peak
        peak = np.abs(window).max()

        # Update noise baseline (slow exponential moving average)
        silence_threshold = 500  # RMS
        if rms < silence_threshold:
            self.noise_baseline = self.noise_baseline * 0.99 + rms * 0.01

        # Signal-to-noise ratio
        snr = rms / max(self.noise_baseline, 1.0)

        # Clipping detection (saturated audio)
        clipping = peak > 32700  # Near int16 max

        return AudioMetrics(
            rms_level=float(rms),
            peak=float(peak),
            noise_floor=self.noise_baseline,
            signal_to_noise=float(snr),
            clipping_detected=clipping,
        )

class StreamingOptimizer:
    """Optimize token streaming for speech synthesis."""

    def __init__(self, target_chunk_size: int = 3):
        """
        target_chunk_size: words per chunk for natural speech pacing.
        3-5 words per chunk = ~300-600ms, optimal for natural flow.
        """
        self.target_chunk_size = target_chunk_size
        self.word_buffer: list[str] = []

    async def optimize(self, token_stream: AsyncGenerator) -> AsyncGenerator:
        """Buffer tokens into natural chunks for TTS."""
        async for token in token_stream:
            self.word_buffer.append(token)

            if len(self.word_buffer) >= self.target_chunk_size:
                chunk = " ".join(self.word_buffer)
                self.word_buffer.clear()
                yield chunk

        # Flush remaining
        if self.word_buffer:
            yield " ".join(self.word_buffer)
            self.word_buffer.clear()

class VoiceCharacteristicsAnalyzer:
    """Analyze voice characteristics from audio metrics (loudness, intensity patterns)."""

    def __init__(self):
        self.characteristic_map = {
            "high_intensity": {"rms_min": 2000, "snr_min": 3.0},
            "low_intensity": {"rms_max": 1000, "snr_min": 0.5},
            "peaky": {"rms_min": 1500, "peak_min": 20000},
        }

    def analyze_from_metrics(self, metrics: AudioMetrics) -> dict[str, float]:
        """Return voice characteristic scores [0..1] based on audio metrics."""
        scores = {
            "high_intensity": min(1.0, max(0.0, (metrics.rms_level - 2000) / 3000)),
            "low_intensity": min(1.0, max(0.0, 1.0 - (metrics.rms_level / 1500))),
            "peaky": min(1.0, max(0.0, (metrics.peak - 15000) / 10000)),
        }
        # Normalize to sum to ~1.0
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        return scores


class AdaptiveVADThreshold:
    """Dynamic VAD threshold that tracks ambient noise floor in real time.

    Replaces the fixed ``RMS_THRESH`` constant with a value that adapts to the
    current acoustic environment, reducing false triggers in noisy rooms while
    remaining sensitive enough to catch soft speech in quiet rooms.

    Threshold = clamp(noise_floor × MULTIPLIER, MIN_THRESH, MAX_THRESH)
    """

    MULTIPLIER: float = 3.0   # How many × above noise floor counts as speech
    MIN_THRESH: float = 400.0  # Never drop below this (prevents over-sensitivity)
    MAX_THRESH: float = 1400.0  # Never exceed this (prevents deafness)

    def __init__(self, initial_noise_floor: float = 150.0) -> None:
        self._analyzer = VoiceMetricsAnalyzer()
        self._analyzer.noise_baseline = initial_noise_floor

    def update(self, audio_chunk: np.ndarray) -> AudioMetrics:
        """Ingest a new audio frame and return quality metrics."""
        return self._analyzer.analyze(audio_chunk)

    @property
    def threshold(self) -> float:
        """Current effective VAD activation threshold (RMS units)."""
        raw = self._analyzer.noise_baseline * self.MULTIPLIER
        return max(self.MIN_THRESH, min(self.MAX_THRESH, raw))

    @property
    def noise_baseline(self) -> float:
        """Estimated ambient noise floor (RMS units)."""
        return self._analyzer.noise_baseline

