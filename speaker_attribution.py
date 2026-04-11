"""
Speaker Attribution System
Attributes transcript segments to specific speakers
"""
import re
from typing import List, Dict, Tuple

class SpeakerAttribution:
    """
    Attribute transcript segments to speakers
    
    Addresses the gap: Everything showing as "User: 100%"
    """
    
    def __init__(self):
        self.speaker_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*:',  # "John Smith:"
            r'([A-Z][a-z]+)\s+(?:said|mentioned|stated|explained|noted|added)',  # "John said"
            r'(?:thank you|thanks)\s+([A-Z][a-z]+)',  # "thank you John"
        ]
    
    def extract_speakers_from_transcript(self, transcript: str, known_participants: List[str] = None) -> Dict:
        """
        Extract speaker information from transcript
        
        Returns:
            {
                'speakers': ['Alice', 'Bob', 'Charlie'],
                'segments': [
                    {'speaker': 'Alice', 'text': '...', 'start': 0, 'end': 100},
                    ...
                ],
                'speaker_stats': {
                    'Alice': {'word_count': 150, 'percentage': 45.5},
                    ...
                }
            }
        """
        if not known_participants:
            known_participants = []
        
        # Extract all mentioned names
        mentioned_names = set()
        
        for pattern in self.speaker_patterns:
            matches = re.findall(pattern, transcript)
            mentioned_names.update(matches)
        
        # Combine with known participants
        all_speakers = list(set(known_participants + list(mentioned_names)))
        
        if not all_speakers:
            # Fallback: single speaker
            return self._single_speaker_fallback(transcript)
        
        # Extract segments per speaker
        segments = self._extract_segments(transcript, all_speakers)
        
        # Calculate statistics
        stats = self._calculate_stats(segments, transcript)
        
        return {
            'speakers': all_speakers,
            'segments': segments,
            'speaker_stats': stats
        }
    
    def _extract_segments(self, transcript: str, speakers: List[str]) -> List[Dict]:
        """Extract text segments for each speaker"""
        segments = []
        
        # Try pattern: "Name: text"
        pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*:\s*([^\.]+(?:\.[^\.]+)*?)(?=\n|$|[A-Z][a-z]+\s*:)'
        
        matches = re.finditer(pattern, transcript, re.MULTILINE)
        
        for match in matches:
            speaker = match.group(1)
            text = match.group(2).strip()
            
            if speaker in speakers and text:
                segments.append({
                    'speaker': speaker,
                    'text': text,
                    'start': match.start(),
                    'end': match.end()
                })
        
        # If no segments found, try other patterns
        if not segments:
            segments = self._extract_segments_alternative(transcript, speakers)
        
        return segments
    
    def _extract_segments_alternative(self, transcript: str, speakers: List[str]) -> List[Dict]:
        """Alternative segment extraction using mentions"""
        segments = []
        
        for speaker in speakers:
            # Find sentences mentioning this speaker
            pattern = rf'\b{re.escape(speaker)}\s+(?:said|mentioned|stated|will|should|needs)\s+([^\.]+\.)'
            
            matches = re.finditer(pattern, transcript, re.IGNORECASE)
            
            for match in matches:
                text = match.group(1).strip()
                
                segments.append({
                    'speaker': speaker,
                    'text': text,
                    'start': match.start(),
                    'end': match.end()
                })
        
        return segments
    
    def _calculate_stats(self, segments: List[Dict], transcript: str) -> Dict:
        """Calculate speaking statistics per speaker"""
        stats = {}
        total_words = len(transcript.split())
        
        # Count words per speaker
        speaker_words = {}
        
        for segment in segments:
            speaker = segment['speaker']
            words = len(segment['text'].split())
            
            if speaker not in speaker_words:
                speaker_words[speaker] = 0
            
            speaker_words[speaker] += words
        
        # Calculate percentages
        for speaker, word_count in speaker_words.items():
            percentage = (word_count / total_words * 100) if total_words > 0 else 0
            
            stats[speaker] = {
                'word_count': word_count,
                'percentage': round(percentage, 1)
            }
        
        return stats
    
    def _single_speaker_fallback(self, transcript: str) -> Dict:
        """Fallback for single speaker"""
        return {
            'speakers': ['Speaker'],
            'segments': [{
                'speaker': 'Speaker',
                'text': transcript,
                'start': 0,
                'end': len(transcript)
            }],
            'speaker_stats': {
                'Speaker': {
                    'word_count': len(transcript.split()),
                    'percentage': 100.0
                }
            }
        }
    
    def format_with_attribution(self, transcript: str, speakers: List[str] = None) -> str:
        """
        Format transcript with speaker attribution
        
        Returns formatted transcript:
        "Alice: We decided to use PostgreSQL.
         Bob: I agree with that decision."
        """
        attribution = self.extract_speakers_from_transcript(transcript, speakers)
        
        if not attribution['segments']:
            return transcript
        
        # Format segments
        formatted_lines = []
        
        for segment in attribution['segments']:
            formatted_lines.append(f"{segment['speaker']}: {segment['text']}")
        
        return '\n\n'.join(formatted_lines)
    
    def get_speaker_summary(self, transcript: str, speakers: List[str] = None) -> str:
        """Get a summary of speaker participation"""
        attribution = self.extract_speakers_from_transcript(transcript, speakers)
        
        summary_lines = [
            "="*70,
            "SPEAKER PARTICIPATION",
            "="*70,
            ""
        ]
        
        for speaker in attribution['speakers']:
            stats = attribution['speaker_stats'].get(speaker, {'word_count': 0, 'percentage': 0})
            
            summary_lines.append(
                f"{speaker}: {stats['word_count']} words ({stats['percentage']}%)"
            )
        
        summary_lines.append("="*70)
        
        return '\n'.join(summary_lines)


# Example usage
if __name__ == "__main__":
    attributor = SpeakerAttribution()
    
    # Test with sample transcript
    transcript = """
    Alice: We decided to use PostgreSQL as our primary database.
    Bob said he agrees with that decision.
    Alice will set up the database by Friday.
    Charlie mentioned that we should also consider Redis for caching.
    Bob: I can help with the Redis setup.
    """
    
    print("="*70)
    print("SPEAKER ATTRIBUTION TEST")
    print("="*70)
    
    # Extract speakers
    result = attributor.extract_speakers_from_transcript(transcript, ['Alice', 'Bob', 'Charlie'])
    
    print(f"\nDetected speakers: {', '.join(result['speakers'])}")
    print(f"\nSegments found: {len(result['segments'])}")
    
    print("\nSpeaker statistics:")
    for speaker, stats in result['speaker_stats'].items():
        print(f"  {speaker}: {stats['word_count']} words ({stats['percentage']}%)")
    
    print("\n" + "="*70)
    print("FORMATTED TRANSCRIPT")
    print("="*70)
    
    formatted = attributor.format_with_attribution(transcript, ['Alice', 'Bob', 'Charlie'])
    print(formatted)
    
    print("\n" + attributor.get_speaker_summary(transcript, ['Alice', 'Bob', 'Charlie']))
