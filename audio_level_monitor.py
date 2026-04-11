"""
Audio Level Monitor and Normalizer
Detects low audio levels and applies normalization
"""
import numpy as np
import wave
import struct

class AudioLevelMonitor:
    """
    Monitor audio levels and normalize if too low
    
    Handles:
    - Low volume detection
    - Audio normalization
    - Level warnings
    """
    
    def __init__(self):
        self.min_acceptable_level = 0.1  # 10% of max
        self.target_level = 0.7  # 70% of max
        self.history = []
        self.max_history = 10
    
    def analyze_audio_level(self, audio_data: bytes, sample_width: int = 2) -> dict:
        """
        Analyze audio level from raw audio data
        
        Args:
            audio_data: Raw audio bytes
            sample_width: Bytes per sample (2 for 16-bit)
        
        Returns:
            {
                'level': 0.0-1.0,
                'is_low': bool,
                'is_silent': bool,
                'recommendation': str
            }
        """
        # Convert bytes to numpy array
        if sample_width == 2:
            # 16-bit audio
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
        else:
            # 8-bit audio
            audio_array = np.frombuffer(audio_data, dtype=np.uint8)
        
        # Calculate RMS (Root Mean Square) level
        rms = np.sqrt(np.mean(audio_array.astype(float)**2))
        
        # Normalize to 0-1 range
        max_value = 32768 if sample_width == 2 else 128
        level = rms / max_value
        
        # Add to history
        self.history.append(level)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        # Calculate average level
        avg_level = np.mean(self.history) if self.history else level
        
        # Determine status
        is_silent = level < 0.01  # Less than 1%
        is_low = level < self.min_acceptable_level and not is_silent
        
        # Generate recommendation
        recommendation = self._get_recommendation(level, avg_level, is_silent, is_low)
        
        return {
            'level': float(level),
            'avg_level': float(avg_level),
            'is_low': is_low,
            'is_silent': is_silent,
            'recommendation': recommendation
        }
    
    def _get_recommendation(self, level: float, avg_level: float, 
                           is_silent: bool, is_low: bool) -> str:
        """Generate recommendation based on audio level"""
        
        if is_silent:
            return "⚠️  SILENT: No audio detected. Check if meeting audio is playing."
        
        if is_low:
            if avg_level < 0.05:
                return "❌ VERY LOW: Increase system volume to at least 50%"
            elif avg_level < 0.1:
                return "⚠️  LOW: Increase system volume to 30-50% for better accuracy"
            else:
                return "💡 ACCEPTABLE: Audio level is low but usable"
        
        if level > 0.9:
            return "⚠️  TOO LOUD: Reduce volume to prevent distortion"
        
        if level > 0.5:
            return "✅ EXCELLENT: Audio level is optimal"
        
        return "✅ GOOD: Audio level is acceptable"
    
    def normalize_audio(self, audio_data: bytes, sample_width: int = 2, 
                       target_level: float = None) -> bytes:
        """
        Normalize audio to target level
        
        Args:
            audio_data: Raw audio bytes
            sample_width: Bytes per sample
            target_level: Target level (0.0-1.0), defaults to self.target_level
        
        Returns:
            Normalized audio bytes
        """
        if target_level is None:
            target_level = self.target_level
        
        # Convert bytes to numpy array
        if sample_width == 2:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            max_value = 32768
        else:
            audio_array = np.frombuffer(audio_data, dtype=np.uint8)
            max_value = 128
        
        # Calculate current level
        current_max = np.max(np.abs(audio_array))
        
        if current_max == 0:
            # Silent audio, return as-is
            return audio_data
        
        # Calculate gain needed
        target_max = max_value * target_level
        gain = target_max / current_max
        
        # Limit gain to prevent over-amplification
        gain = min(gain, 10.0)  # Max 10x amplification
        
        # Apply gain
        normalized = audio_array * gain
        
        # Clip to prevent overflow
        normalized = np.clip(normalized, -max_value + 1, max_value - 1)
        
        # Convert back to bytes
        if sample_width == 2:
            return normalized.astype(np.int16).tobytes()
        else:
            return normalized.astype(np.uint8).tobytes()
    
    def should_normalize(self, level: float) -> bool:
        """Check if audio should be normalized"""
        return level < self.min_acceptable_level and level > 0.01
    
    def get_status_display(self, level: float) -> str:
        """Get visual status display"""
        # Create level bar
        bar_length = 20
        filled = int(level * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        # Color code
        if level < 0.05:
            status = "❌ VERY LOW"
        elif level < 0.1:
            status = "⚠️  LOW"
        elif level < 0.3:
            status = "💡 ACCEPTABLE"
        elif level < 0.7:
            status = "✅ GOOD"
        elif level < 0.9:
            status = "✅ EXCELLENT"
        else:
            status = "⚠️  TOO LOUD"
        
        return f"[{bar}] {level*100:.1f}% {status}"


# Example usage
if __name__ == "__main__":
    import pyaudio
    
    monitor = AudioLevelMonitor()
    
    print("="*70)
    print("🎤 AUDIO LEVEL MONITOR TEST")
    print("="*70)
    print("\nRecording 3 seconds of audio to test levels...")
    
    # Record sample audio
    audio = pyaudio.PyAudio()
    
    try:
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        frames = []
        for _ in range(0, int(16000 / 1024 * 3)):  # 3 seconds
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        # Analyze
        audio_data = b''.join(frames)
        result = monitor.analyze_audio_level(audio_data)
        
        print("\n" + "="*70)
        print("ANALYSIS RESULTS")
        print("="*70)
        print(f"\nLevel: {result['level']*100:.1f}%")
        print(f"Average: {result['avg_level']*100:.1f}%")
        print(f"Status: {monitor.get_status_display(result['level'])}")
        print(f"\n{result['recommendation']}")
        
        if monitor.should_normalize(result['level']):
            print("\n🔧 Applying normalization...")
            normalized = monitor.normalize_audio(audio_data)
            
            result_after = monitor.analyze_audio_level(normalized)
            print(f"After normalization: {result_after['level']*100:.1f}%")
            print(f"Status: {monitor.get_status_display(result_after['level'])}")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Make sure a microphone is connected")
    
    finally:
        audio.terminate()
