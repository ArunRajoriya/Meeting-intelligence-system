"""
Consolidated Utilities Module
Combines: context_manager, transcript_corrector, transcript_cleaner, speaker_attribution
"""
from typing import Dict, List, Optional
from collections import deque
import re

# ============================================
# CONTEXT MANAGER
# ============================================

class ContextManager:
    """Manages conversation context across meeting chunks"""
    
    def __init__(self, max_decisions: int = 20, max_actions: int = 30):
        self.decisions = deque(maxlen=max_decisions)
        self.action_items = deque(maxlen=max_actions)
        self.topics = deque(maxlen=10)
        self.speakers = set()
        self.meeting_metadata = {}
        self.current_topic = None
        self.topic_transitions = []
    
    def add_decision(self, decision: str, priority: str = 'medium'):
        """Add a decision to context"""
        self.decisions.append({
            'decision': decision,
            'priority': priority,
            'timestamp': self._get_timestamp()
        })
    
    def add_action_item(self, task: str, owner: str = "", deadline: str = ""):
        """Add action item to context"""
        self.action_items.append({
            'task': task,
            'owner': owner,
            'deadline': deadline,
            'timestamp': self._get_timestamp()
        })
    
    def add_topic(self, topic: str):
        """Track discussion topics"""
        if topic != self.current_topic:
            if self.current_topic:
                self.topic_transitions.append({
                    'from': self.current_topic,
                    'to': topic,
                    'timestamp': self._get_timestamp()
                })
            self.current_topic = topic
            self.topics.append(topic)
    
    def add_speaker(self, speaker: str):
        """Track speakers"""
        self.speakers.add(speaker)
    
    def set_metadata(self, key: str, value):
        """Set meeting metadata"""
        self.meeting_metadata[key] = value
    
    def get_context_summary(self) -> str:
        """Get formatted context summary for AI prompts"""
        context_parts = []
        
        if self.decisions:
            context_parts.append("PREVIOUS DECISIONS IN THIS MEETING:")
            for i, dec in enumerate(list(self.decisions)[-5:], 1):
                priority_marker = "🔥" if dec['priority'] == 'high' else "📌"
                context_parts.append(f"  {priority_marker} {dec['decision']}")
        
        if self.action_items:
            context_parts.append("\nPENDING ACTION ITEMS:")
            for i, action in enumerate(list(self.action_items)[-5:], 1):
                owner_str = f"[{action['owner']}]" if action['owner'] else "[Unassigned]"
                context_parts.append(f"  • {owner_str} {action['task']}")
        
        if self.topics:
            context_parts.append("\nDISCUSSION TOPICS:")
            context_parts.append(f"  Current: {self.current_topic}")
            if len(self.topics) > 1:
                context_parts.append(f"  Previous: {', '.join(list(self.topics)[-4:-1])}")
        
        if self.speakers:
            context_parts.append(f"\nPARTICIPANTS: {', '.join(sorted(self.speakers))}")
        
        return "\n".join(context_parts)
    
    def get_context_for_prompt(self, include_metadata: bool = True) -> str:
        """Get context formatted for AI prompt"""
        prompt_parts = []
        
        if include_metadata and self.meeting_metadata:
            prompt_parts.append("MEETING CONTEXT:")
            for key, value in self.meeting_metadata.items():
                prompt_parts.append(f"  {key}: {value}")
            prompt_parts.append("")
        
        prompt_parts.append(self.get_context_summary())
        
        prompt_parts.append("\nIMPORTANT:")
        prompt_parts.append("- Consider previous decisions when analyzing current discussion")
        prompt_parts.append("- Reference earlier action items if relevant")
        prompt_parts.append("- Maintain consistency with established context")
        
        return "\n".join(prompt_parts)
    
    def clear_context(self):
        """Clear all context (for new meeting)"""
        self.decisions.clear()
        self.action_items.clear()
        self.topics.clear()
        self.speakers.clear()
        self.meeting_metadata.clear()
        self.current_topic = None
        self.topic_transitions.clear()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")


# ============================================
# TRANSCRIPT CORRECTOR
# ============================================

class TranscriptCorrector:
    """Corrects common transcription errors and standardizes terminology"""
    
    def __init__(self):
        self.error_corrections = {
            'infrared dev': 'infrastructure dev',
            'infrared development': 'infrastructure development',
            'get ops': 'GitOps',
            'git ops': 'GitOps',
            'cube con': 'KubeCon',
            'on call': 'on-call',
            'off site': 'offsite',
            'stand up': 'standup',
            'check in': 'check-in',
            'follow up': 'follow-up',
        }
        
        self.domain_corrections = {
            'engineering': {
                'S1': 'Severity 1 (S1)',
                'S2': 'Severity 2 (S2)',
                'P0': 'Priority 0 (P0)',
                'P1': 'Priority 1 (P1)',
            },
            'business': {
                'Q1': 'Q1',
                'Q2': 'Q2',
                'Q3': 'Q3',
                'Q4': 'Q4',
            }
        }
        
        self.noise_patterns = [
            r'\b(um+|uh+|ah+|er+|like)\b',
            r'\[inaudible\]',
            r'\[crosstalk\]',
            r'\[background noise\]',
        ]
    
    def correct(self, transcript: str, domain: str = None) -> str:
        """Correct transcript errors"""
        corrected = transcript
        
        for wrong, right in self.error_corrections.items():
            pattern = re.compile(re.escape(wrong), re.IGNORECASE)
            corrected = pattern.sub(right, corrected)
        
        if domain and domain in self.domain_corrections:
            for wrong, right in self.domain_corrections[domain].items():
                corrected = corrected.replace(wrong, right)
        
        for pattern in self.noise_patterns:
            corrected = re.sub(pattern, '', corrected, flags=re.IGNORECASE)
        
        corrected = re.sub(r'\s+', ' ', corrected)
        corrected = corrected.strip()
        
        return corrected
    
    def correct_with_context(self, transcript: str, meeting_type: str = None) -> str:
        """Context-aware correction based on meeting type"""
        domain_map = {
            'technical': 'engineering',
            'business': 'business',
            'formal': None,
            'casual': None,
        }
        
        domain = domain_map.get(meeting_type)
        return self.correct(transcript, domain)


# ============================================
# TRANSCRIPT CLEANER
# ============================================

class TranscriptCleaner:
    """Cleans and prepares transcripts for analysis"""
    
    def __init__(self):
        self.noise_patterns = [
            (r'(\b(?:thank you|thanks|obrigado|gracias|merci)\b[.,!?]*\s*){3,}', 'Thank you. '),
            (r'(\bthank you\b[.,!?]*\s*)+$', ''),
            (r'\b(um|uh|like|you know)\b\s*', ''),
            (r'\[silence\]|\[inaudible\]|\[unclear\]', ''),
            (r'([.!?])\1+', r'\1'),
        ]
    
    def clean(self, transcript: str) -> str:
        """Clean transcript"""
        if not transcript:
            return transcript
        
        cleaned = ' '.join(transcript.split())
        
        for pattern, replacement in self.noise_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        cleaned = re.sub(r'([.!?])([A-Z])', r'\1 \2', cleaned)
        
        return cleaned.strip()


# ============================================
# SPEAKER ATTRIBUTION
# ============================================

class SpeakerAttributor:
    """Attributes statements to speakers"""
    
    def __init__(self):
        self.speaker_patterns = [
            r'([A-Z][a-z]+)\s*:\s*([^.!?]+[.!?])',
            r'([A-Z][a-z]+)\s+(?:said|mentioned|stated|asked)\s+["\']([^"\']+)["\']',
        ]
    
    def attribute_speakers(self, transcript: str, known_speakers: List[str] = None) -> Dict:
        """Attribute statements to speakers"""
        if known_speakers is None:
            known_speakers = []
        
        attributions = []
        
        for pattern in self.speaker_patterns:
            matches = re.findall(pattern, transcript)
            for speaker, statement in matches:
                if not known_speakers or speaker in known_speakers:
                    attributions.append({
                        'speaker': speaker,
                        'statement': statement.strip()
                    })
        
        return {
            'attributions': attributions,
            'speakers': list(set([a['speaker'] for a in attributions]))
        }
    
    def extract_speaker_names(self, transcript: str) -> List[str]:
        """Extract potential speaker names from transcript"""
        names = set()
        
        for pattern in self.speaker_patterns:
            matches = re.findall(pattern, transcript)
            for speaker, _ in matches:
                if len(speaker) > 2:
                    names.add(speaker)
        
        return list(names)
