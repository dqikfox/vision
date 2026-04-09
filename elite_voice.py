"""
elite_voice.py — Advanced voice pipeline, buffering, emotion detection
======================================================================
Streaming optimization, audio quality metrics, speaking style adaptation.
"""

import asyncio
import numpy as np
from collections import deque
from dataclasses import dataclass
from typing import AsyncGenerator

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

class EmotionDetector:
    """Detect emotion/intent from user audio (basic heuristics)."""
    
    def __init__(self):
        self.emotion_map = {
            "anger": {"rms_min": 2000, "snr_min": 3.0},
            "question": {},  # Detected from pitch rise (simplified)
            "calm": {"rms_max": 1000, "snr_min": 0.5},
            "excited": {"rms_min": 1500, "peak_min": 20000},
        }
    
    def detect_from_metrics(self, metrics: AudioMetrics) -> dict[str, float]:
        """Return emotion scores [0..1] based on audio metrics."""
        scores = {
            "anger": min(1.0, max(0.0, (metrics.rms_level - 2000) / 3000)),
            "calm": min(1.0, max(0.0, 1.0 - (metrics.rms_level / 1500))),
            "excited": min(1.0, max(0.0, (metrics.peak - 15000) / 10000)),
        }
        # Normalize to sum to ~1.0
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        return scores

class SpeakingStyleAdapter:
    """Adapt response based on user emotion/style."""
    
    def __init__(self):
        self.emotion_prompts = {
            "anger": "Respond calmly and professionally, de-escalate.",
            "excited": "Match the energy! Be upbeat and enthusiastic.",
            "calm": "Speak slowly and thoughtfully. Be reassuring.",
            "question": "Provide a clear, concise answer with examples.",
        }
    
    def get_system_prompt_modifier(self, emotion_scores: dict[str, float]) -> str:
        """Return system prompt modifier based on detected emotion."""
        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
        return self.emotion_prompts.get(dominant_emotion, "")
    
    def adapt_tts_params(self, emotion_scores: dict[str, float]) -> dict:
        """Adjust TTS parameters (rate, pitch) based on emotion."""
        if emotion_scores.get("excited", 0) > 0.6:
            return {"rate": 185, "pitch": 1.2}  # Faster, higher pitch
        elif emotion_scores.get("calm", 0) > 0.6:
            return {"rate": 150, "pitch": 0.9}  # Slower, lower pitch
        else:
            return {"rate": 175, "pitch": 1.0}  # Normal
