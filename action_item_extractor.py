"""
PRODUCTION-GRADE Action Item Extractor
Implements strict filtering to avoid false positives
"""
import re
from typing import List, Dict

class ActionItemExtractor:
    """
    Extract action items with STRICT validation
    
    Prevents false positives by:
    - Requiring explicit action verbs
    - Validating sentence structure
    - Confidence scoring
    - Filtering general statements
    """
    
    def __init__(self):
        # STRICT action indicators
        self.action_verbs = [
            'will', 'should', 'must', 'needs to', 'has to',
            'going to', 'plan to', 'commit to', 'agree to',
            'assigned to', 'responsible for'
        ]
        
        # Words that indicate NOT an action
        self.exclusion_words = [
            'we discussed', 'we talked', 'mentioned', 'said',
            'think', 'believe', 'feel', 'hope', 'wish',
            'maybe', 'perhaps', 'possibly', 'might'
        ]
    
    def extract_action_items(self, transcript: str, participants: List[str]) -> List[Dict]:
        """
        Extract action items with STRICT filtering
        
        Returns:
            List of validated action items with confidence scores
        """
        sentences = self._split_into_sentences(transcript)
        
        action_items = []
        
        for sentence in sentences:
            # Check if this is a valid action
            if not self._is_valid_action(sentence):
                continue
            
            # Extract components
            owner = self._extract_owner(sentence, participants)
            deadline = self._extract_deadline(sentence)
            confidence = self._calculate_confidence(sentence, owner, deadline)
            
            # Only include if confidence is reasonable
            if confidence >= 0.3:  # Minimum 30% confidence
                action_items.append({
                    'task': sentence.strip(),
                    'owner': owner,
                    'deadline': deadline,
                    'confidence': confidence,
                    'confidence_label': self._confidence_label(confidence)
                })
        
        # Sort by confidence (highest first)
        action_items.sort(key=lambda x: x['confidence'], reverse=True)
        
        return action_items
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Split on period, exclamation, question mark
        sentences = re.split(r'[.!?]+', text)
        
        # Clean and filter
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        return sentences
    
    def _is_valid_action(self, sentence: str) -> bool:
        """
        STRICT VALIDATION: Is this a real action item?
        
        Returns True only if:
        1. Contains action verb
        2. Does NOT contain exclusion words
        3. Is specific enough (not too vague)
        """
        sentence_lower = sentence.lower()
        
        # Must contain action verb
        has_action_verb = any(verb in sentence_lower for verb in self.action_verbs)
        if not has_action_verb:
            return False
        
        # Must NOT contain exclusion words
        has_exclusion = any(word in sentence_lower for word in self.exclusion_words)
        if has_exclusion:
            return False
        
        # Must be specific enough (at least 5 words)
        if len(sentence.split()) < 5:
            return False
        
        # Must not be too vague
        vague_patterns = [
            r'^\s*(?:we|they|someone)\s+(?:will|should|must)\s+(?:do|work|handle)\s+(?:it|this|that|something)',
            r'^\s*(?:need|needs)\s+to\s+(?:be|get)\s+done',
        ]
        
        for pattern in vague_patterns:
            if re.match(pattern, sentence_lower):
                return False
        
        return True
    
    def _extract_owner(self, sentence: str, participants: List[str]) -> str:
        """
        Extract owner from sentence
        
        Patterns:
        - "John will do X"
        - "Sarah needs to complete Y"
        - "Mike should review Z"
        """
        # Try to find participant names
        for participant in participants:
            # Pattern: "Name will/should/must/needs"
            pattern = rf'\b{re.escape(participant)}\s+(?:will|should|must|needs?)\b'
            if re.search(pattern, sentence, re.IGNORECASE):
                return participant
        
        # Try to extract name before action verb
        for verb in self.action_verbs:
            pattern = rf'\b([A-Z][a-z]+)\s+{re.escape(verb)}\b'
            match = re.search(pattern, sentence)
            if match:
                name = match.group(1)
                # Validate it's a reasonable name (not a common word)
                if len(name) > 2 and name not in ['The', 'This', 'That', 'They', 'We']:
                    return name
        
        return None
    
    def _extract_deadline(self, sentence: str) -> str:
        """
        Extract deadline from sentence
        
        Patterns:
        - "by Friday"
        - "next week"
        - "tomorrow"
        - "end of month"
        - "by May 8th"
        """
        deadline_patterns = [
            r'by\s+([A-Z][a-z]+day)',  # by Friday
            r'by\s+([A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?)',  # by May 8th
            r'by\s+(tomorrow|today)',
            r'(next\s+(?:week|month|Monday|Tuesday|Wednesday|Thursday|Friday))',
            r'(end\s+of\s+(?:week|month|quarter|year))',
            r'(this\s+(?:week|month|Friday|Monday))',
            r'by\s+the\s+end\s+of\s+([A-Z][a-z]+)',  # by the end of March
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        
        return None
    
    def _calculate_confidence(self, sentence: str, owner: str, deadline: str) -> float:
        """
        Calculate confidence score for action item
        
        Factors:
        - Has owner: +0.4
        - Has deadline: +0.3
        - Has strong action verb: +0.2
        - Is specific: +0.1
        """
        confidence = 0.0
        
        # Owner present
        if owner:
            confidence += 0.4
        
        # Deadline present
        if deadline:
            confidence += 0.3
        
        # Strong action verb
        strong_verbs = ['will', 'must', 'assigned', 'responsible']
        if any(verb in sentence.lower() for verb in strong_verbs):
            confidence += 0.2
        
        # Specificity (has numbers, dates, or specific nouns)
        if re.search(r'\d+', sentence):  # Has numbers
            confidence += 0.05
        if re.search(r'\b(?:complete|finish|deliver|submit|review|approve)\b', sentence, re.IGNORECASE):
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _confidence_label(self, confidence: float) -> str:
        """Convert confidence score to label"""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        else:
            return "low"
    
    def filter_by_confidence(self, action_items: List[Dict], min_confidence: float = 0.5) -> List[Dict]:
        """Filter action items by minimum confidence"""
        return [item for item in action_items if item['confidence'] >= min_confidence]


# Example usage
if __name__ == "__main__":
    extractor = ActionItemExtractor()
    
    # Test cases
    test_transcript = """
    John will complete the API design by Friday.
    Sarah needs to review the database schema by next week.
    We discussed the project timeline.
    Mike should deploy to staging tomorrow.
    Someone will handle the testing.
    The team will work on improvements.
    """
    
    participants = ["John", "Sarah", "Mike"]
    
    actions = extractor.extract_action_items(test_transcript, participants)
    
    print("Extracted Action Items:")
    for i, action in enumerate(actions, 1):
        print(f"\n{i}. {action['task']}")
        print(f"   Owner: {action['owner']}")
        print(f"   Deadline: {action['deadline']}")
        print(f"   Confidence: {action['confidence']:.2f} ({action['confidence_label']})")
    
    print(f"\n\nHigh confidence actions (>=0.5):")
    high_conf = extractor.filter_by_confidence(actions, 0.5)
    print(f"Found {len(high_conf)} out of {len(actions)} total")
