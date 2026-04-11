"""
Formal Meeting Context Detector
Identifies formal meetings (council hearings, board meetings, etc.)
and extracts procedural information
"""
import re
from typing import Dict, List

class FormalMeetingDetector:
    """Detect and extract formal meeting procedures"""
    
    def __init__(self):
        self.formal_indicators = [
            'hearing', 'submission', 'annual plan', 'council',
            'board meeting', 'reconvening', 'deliberations',
            'conflict of interest', 'register', 'chair',
            'motion', 'seconded', 'vote', 'resolution'
        ]
        
        self.procedural_actions = [
            'conflict of interest',
            'motion',
            'seconded',
            'vote',
            'approved',
            'rejected',
            'tabled',
            'deferred'
        ]
    
    def detect_formal_meeting(self, transcript: str) -> Dict:
        """
        Detect if this is a formal meeting and extract context
        
        Returns:
            {
                'is_formal': bool,
                'meeting_type': str,
                'procedural_items': List[Dict],
                'confidence': float
            }
        """
        transcript_lower = transcript.lower()
        
        # Count formal indicators
        indicator_count = sum(
            1 for indicator in self.formal_indicators 
            if indicator in transcript_lower
        )
        
        # Determine if formal
        is_formal = indicator_count >= 3
        confidence = min(indicator_count / 10.0, 1.0)
        
        # Determine meeting type
        meeting_type = self._determine_meeting_type(transcript_lower)
        
        # Extract procedural items
        procedural_items = self._extract_procedural_items(transcript)
        
        return {
            'is_formal': is_formal,
            'meeting_type': meeting_type,
            'procedural_items': procedural_items,
            'confidence': confidence,
            'indicator_count': indicator_count
        }
    
    def _determine_meeting_type(self, transcript_lower: str) -> str:
        """Determine the type of formal meeting"""
        if 'hearing' in transcript_lower and 'submission' in transcript_lower:
            return 'Public Hearing'
        elif 'council' in transcript_lower:
            return 'Council Meeting'
        elif 'board' in transcript_lower:
            return 'Board Meeting'
        elif 'annual plan' in transcript_lower:
            return 'Annual Plan Review'
        else:
            return 'Formal Meeting'
    
    def _extract_procedural_items(self, transcript: str) -> List[Dict]:
        """Extract procedural items like conflicts of interest, motions, etc."""
        items = []
        
        # Conflict of interest pattern
        coi_pattern = r'(?:express|register|declare)\s+(?:a\s+)?conflict\s+of\s+interest'
        for match in re.finditer(coi_pattern, transcript, re.IGNORECASE):
            context = self._get_context(transcript, match.start(), 100)
            items.append({
                'type': 'Conflict of Interest',
                'context': context,
                'position': match.start()
            })
        
        # Motion pattern
        motion_pattern = r'(?:move|motion)\s+that'
        for match in re.finditer(motion_pattern, transcript, re.IGNORECASE):
            context = self._get_context(transcript, match.start(), 150)
            items.append({
                'type': 'Motion',
                'context': context,
                'position': match.start()
            })
        
        # Vote pattern
        vote_pattern = r'(?:all\s+in\s+favor|those\s+in\s+favor|vote|carried|passed)'
        for match in re.finditer(vote_pattern, transcript, re.IGNORECASE):
            context = self._get_context(transcript, match.start(), 100)
            items.append({
                'type': 'Vote',
                'context': context,
                'position': match.start()
            })
        
        return items
    
    def _get_context(self, text: str, position: int, length: int) -> str:
        """Get context around a position"""
        start = max(0, position - length // 2)
        end = min(len(text), position + length // 2)
        return text[start:end].strip()
    
    def generate_formal_summary(self, transcript: str, 
                                meeting_info: Dict) -> str:
        """Generate a summary appropriate for formal meetings"""
        if not meeting_info['is_formal']:
            return None
        
        summary_parts = []
        
        # Meeting type
        summary_parts.append(f"This {meeting_info['meeting_type']} ")
        
        # Procedural items
        if meeting_info['procedural_items']:
            coi_count = sum(1 for item in meeting_info['procedural_items'] 
                          if item['type'] == 'Conflict of Interest')
            if coi_count > 0:
                summary_parts.append(f"included {coi_count} conflict of interest declaration(s). ")
            
            motion_count = sum(1 for item in meeting_info['procedural_items'] 
                             if item['type'] == 'Motion')
            if motion_count > 0:
                summary_parts.append(f"{motion_count} motion(s) were presented. ")
        
        return ''.join(summary_parts)


# Example usage
if __name__ == "__main__":
    detector = FormalMeetingDetector()
    
    sample_transcript = """
    Thank you chair. We're reconvening the hearing for submissions on the 
    annual plan 2021. Roger, may I express a conflict of interest with the 
    Cambridge Museum Trust submission. Mike also registered a conflict of 
    interest as a trust board member. We'll now hear from Harriet Dixon 
    presenting the Cambridge Community House Trust submission.
    """
    
    result = detector.detect_formal_meeting(sample_transcript)
    
    print(f"Is Formal: {result['is_formal']}")
    print(f"Meeting Type: {result['meeting_type']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"\nProcedural Items:")
    for item in result['procedural_items']:
        print(f"  - {item['type']}: {item['context'][:80]}...")
    
    summary = detector.generate_formal_summary(sample_transcript, result)
    if summary:
        print(f"\nFormal Summary: {summary}")
