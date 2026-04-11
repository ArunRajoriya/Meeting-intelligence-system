"""
PRODUCTION: Speaker Diarization System
Identifies and separates multiple speakers in audio
Uses: pyannote.audio for state-of-the-art speaker separation
"""
import os
import tempfile
from typing import List, Dict, Tuple
import torch

class SpeakerDiarization:
    """
    Separate and identify multiple speakers in audio
    
    Uses pyannote.audio - state-of-the-art speaker diarization
    """
    
    def __init__(self, hf_token: str = None):
        """
        Initialize speaker diarization
        
        Args:
            hf_token: HuggingFace token for pyannote models
                     Get from: https://huggingface.co/settings/tokens
        """
        self.hf_token = hf_token or os.getenv('HUGGINGFACE_TOKEN')
        self.pipeline = None
        
        if self.hf_token:
            try:
                from pyannote.audio import Pipeline
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self.hf_token
                )
                
                # Use GPU if available
                if torch.cuda.is_available():
                    self.pipeline.to(torch.device("cuda"))
                
                print("✅ Speaker diarization initialized")
            except Exception as e:
                print(f"⚠️  Speaker diarization not available: {e}")
                print("💡 Install: pip install pyannote.audio")
                print("💡 Get token: https://huggingface.co/settings/tokens")
    
    def diarize(self, audio_file, filename: str = "audio.mp3") -> Dict:
        """
        Perform speaker diarization on audio
        
        Returns:
            {
                'speakers': ['SPEAKER_00', 'SPEAKER_01', ...],
                'segments': [
                    {
                        'start': 0.0,
                        'end': 5.2,
                        'speaker': 'SPEAKER_00',
                        'text': None  # Will be filled by transcription
                    },
                    ...
                ],
                'speaker_count': 3
            }
        """
        if not self.pipeline:
            return self._fallback_single_speaker()
        
        # Save to temp file if needed
        if hasattr(audio_file, 'read'):
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_file.write(audio_file.read())
            temp_file.close()
            audio_path = temp_file.name
            audio_file.seek(0)  # Reset for later use
        else:
            audio_path = audio_file
        
        try:
            # Run diarization
            diarization = self.pipeline(audio_path)
            
            # Extract segments
            segments = []
            speakers = set()
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    'start': turn.start,
                    'end': turn.end,
                    'speaker': speaker,
                    'text': None
                })
                speakers.add(speaker)
            
            result = {
                'speakers': sorted(list(speakers)),
                'segments': segments,
                'speaker_count': len(speakers)
            }
            
            print(f"✅ Detected {len(speakers)} speakers")
            
            return result
            
        except Exception as e:
            print(f"⚠️  Diarization failed: {e}")
            return self._fallback_single_speaker()
        
        finally:
            # Cleanup temp file
            if hasattr(audio_file, 'read') and os.path.exists(audio_path):
                os.unlink(audio_path)
    
    def _fallback_single_speaker(self) -> Dict:
        """Fallback when diarization not available"""
        return {
            'speakers': ['SPEAKER_00'],
            'segments': [],
            'speaker_count': 1
        }
    
    def assign_names_to_speakers(self, diarization: Dict, 
                                 transcript: str,
                                 known_names: List[str] = None) -> Dict:
        """
        Assign real names to speaker labels
        
        Uses:
        1. Known names from meeting metadata
        2. Name mentions in transcript
        3. Role indicators (Chair, Presenter, etc.)
        """
        if not known_names:
            known_names = []
        
        # Extract names mentioned in transcript
        import re
        
        # Pattern: "Name:" or "Name said" or "Thank you Name"
        name_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*:',  # "John Smith:"
            r'\b([A-Z][a-z]+)\s+(?:said|mentioned|stated)',  # "John said"
            r'thank\s+you\s+([A-Z][a-z]+)',  # "thank you John"
        ]
        
        mentioned_names = set()
        for pattern in name_patterns:
            matches = re.findall(pattern, transcript)
            mentioned_names.update(matches)
        
        # Combine with known names
        all_names = list(set(known_names + list(mentioned_names)))
        
        # Assign names to speakers
        speaker_mapping = {}
        
        for i, speaker_id in enumerate(diarization['speakers']):
            if i < len(all_names):
                speaker_mapping[speaker_id] = all_names[i]
            else:
                # Detect role from context
                role = self._detect_speaker_role(speaker_id, transcript)
                speaker_mapping[speaker_id] = role or f"Speaker {i+1}"
        
        # Update diarization with names
        diarization['speaker_mapping'] = speaker_mapping
        diarization['named_speakers'] = list(speaker_mapping.values())
        
        return diarization
    
    def _detect_speaker_role(self, speaker_id: str, transcript: str) -> str:
        """Detect speaker role from context"""
        role_indicators = {
            'Chair': ['chair', 'chairman', 'chairperson', 'presiding'],
            'Presenter': ['presenting', 'submission', 'on behalf of'],
            'Member': ['member', 'councillor', 'board member'],
        }
        
        transcript_lower = transcript.lower()
        
        for role, indicators in role_indicators.items():
            if any(indicator in transcript_lower for indicator in indicators):
                return role
        
        return None
    
    def merge_with_transcript(self, diarization: Dict, 
                            transcript: str,
                            timestamps: List[Dict] = None) -> str:
        """
        Merge speaker labels with transcript
        
        Returns formatted transcript with speaker labels:
        "SPEAKER_00: Hello everyone..."
        "SPEAKER_01: Thank you for having me..."
        """
        if not diarization['segments'] or not timestamps:
            # Fallback: try to detect speakers from text
            return self._detect_speakers_from_text(transcript, diarization)
        
        # Match transcript segments with speaker segments
        labeled_transcript = []
        
        for segment in diarization['segments']:
            # Find transcript text for this time range
            text = self._get_text_for_timerange(
                segment['start'], 
                segment['end'], 
                timestamps
            )
            
            if text:
                speaker_name = diarization['speaker_mapping'].get(
                    segment['speaker'], 
                    segment['speaker']
                )
                labeled_transcript.append(f"{speaker_name}: {text}")
        
        return '\n\n'.join(labeled_transcript)
    
    def _get_text_for_timerange(self, start: float, end: float, 
                                timestamps: List[Dict]) -> str:
        """Get transcript text for time range"""
        texts = []
        
        for ts in timestamps:
            if ts['start'] >= start and ts['end'] <= end:
                texts.append(ts['text'])
        
        return ' '.join(texts)
    
    def _detect_speakers_from_text(self, transcript: str, 
                                   diarization: Dict) -> str:
        """Fallback: detect speakers from text patterns"""
        import re
        
        # Split by speaker patterns
        pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*:'
        
        parts = re.split(pattern, transcript)
        
        if len(parts) <= 1:
            # No speaker labels found
            return transcript
        
        # Reconstruct with speaker labels
        labeled = []
        current_speaker = None
        
        for i, part in enumerate(parts):
            if i % 2 == 1:  # Speaker name
                current_speaker = part
            elif current_speaker:  # Text
                labeled.append(f"{current_speaker}: {part.strip()}")
        
        return '\n\n'.join(labeled)


# Example usage
if __name__ == "__main__":
    # Initialize
    diarizer = SpeakerDiarization()
    
    # Test with sample audio
    sample_audio = "path/to/meeting.wav"
    
    if diarizer.pipeline:
        # Perform diarization
        result = diarizer.diarize(sample_audio)
        
        print(f"\nDetected {result['speaker_count']} speakers:")
        for speaker in result['speakers']:
            print(f"  - {speaker}")
        
        print(f"\nFound {len(result['segments'])} segments")
        
        # Assign names
        known_names = ["John Smith", "Sarah Johnson", "Mike Chen"]
        transcript = "John: Hello everyone. Sarah said we should start."
        
        result = diarizer.assign_names_to_speakers(result, transcript, known_names)
        
        print(f"\nSpeaker mapping:")
        for speaker_id, name in result['speaker_mapping'].items():
            print(f"  {speaker_id} → {name}")
    else:
        print("⚠️  Diarization not available. Install pyannote.audio")
