"""
Enhanced Decision Classifier
Detects and classifies decisions with high accuracy
"""
import re
from typing import List, Dict, Tuple

class DecisionClassifier:
    """
    Advanced decision detection and classification
    
    Addresses the gap: "Weekend on-call removal" was missed
    """
    
    def __init__(self):
        # High priority decision indicators
        self.high_priority_indicators = {
            'explicit': [
                'decided', 'decision', 'agreed', 'approved', 'confirmed',
                'finalized', 'committed to', 'consensus', 'vote', 'chose'
            ],
            'process_change': [
                'remove', 'add', 'change', 'modify', 'update', 'revise',
                'eliminate', 'introduce', 'implement', 'discontinue'
            ],
            'policy': [
                'policy', 'rule', 'requirement', 'mandate', 'regulation',
                'guideline', 'standard', 'procedure'
            ],
            'legal_compliance': [
                'legal', 'compliance', 'regulatory', 'mandatory', 'required',
                'must', 'shall', 'obligation'
            ]
        }
        
        # Medium priority indicators
        self.medium_priority_indicators = [
            'will', 'going to', 'plan to', 'intend to', 'commit to',
            "let's", "we'll", "we're going to"
        ]
        
        # NOT decision indicators (discussion only)
        self.non_decision_indicators = [
            'should', 'could', 'might', 'maybe', 'perhaps', 'possibly',
            'consider', 'think about', 'discuss', 'explore', 'look into'
        ]
        
        # Engineering context keywords
        self.engineering_keywords = {
            'process': ['on-call', 'escalation', 'workflow', 'pipeline', 'deployment'],
            'technical': ['database', 'api', 'framework', 'architecture', 'infrastructure'],
            'team': ['hiring', 'staffing', 'rotation', 'schedule', 'meeting'],
            'quality': ['testing', 'review', 'qa', 'validation', 'monitoring']
        }
    
    def extract_decisions(self, transcript: str) -> List[Dict]:
        """
        Extract and classify decisions from transcript
        
        Returns:
            [
                {
                    'decision': 'Decision text',
                    'priority': 'high' | 'medium' | 'low',
                    'category': 'process' | 'technical' | 'policy' | 'team',
                    'confidence': 0.0-1.0
                },
                ...
            ]
        """
        decisions = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', transcript)
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            if len(sentence) < 10:
                continue
            
            # Check if it's a decision
            decision_info = self._classify_sentence(sentence)
            
            if decision_info:
                decisions.append(decision_info)
        
        # Sort by priority and confidence
        decisions.sort(key=lambda x: (
            0 if x['priority'] == 'high' else 1 if x['priority'] == 'medium' else 2,
            -x['confidence']
        ))
        
        return decisions
    
    def _classify_sentence(self, sentence: str) -> Dict | None:
        """
        Classify a sentence as decision or not
        
        Returns decision info or None
        """
        sentence_lower = sentence.lower()
        
        # Check for non-decision indicators first
        if any(indicator in sentence_lower for indicator in self.non_decision_indicators):
            # Unless it also has strong decision indicators
            if not any(indicator in sentence_lower for indicator in self.high_priority_indicators['explicit']):
                return None
        
        # Check for high priority decisions
        priority = None
        confidence = 0.0
        category = 'general'
        
        # Explicit decisions (highest priority)
        if any(indicator in sentence_lower for indicator in self.high_priority_indicators['explicit']):
            priority = 'high'
            confidence = 0.9
        
        # Process changes (high priority)
        elif any(indicator in sentence_lower for indicator in self.high_priority_indicators['process_change']):
            # Check if it's about a process/policy
            if any(keyword in sentence_lower for keywords in self.engineering_keywords.values() for keyword in keywords):
                priority = 'high'
                confidence = 0.85
                category = 'process'
        
        # Policy/legal (high priority)
        elif any(indicator in sentence_lower for indicator in self.high_priority_indicators['policy']):
            priority = 'high'
            confidence = 0.9
            category = 'policy'
        
        elif any(indicator in sentence_lower for indicator in self.high_priority_indicators['legal_compliance']):
            priority = 'high'
            confidence = 0.95
            category = 'legal'
        
        # Medium priority (will/going to)
        elif any(indicator in sentence_lower for indicator in self.medium_priority_indicators):
            priority = 'medium'
            confidence = 0.7
        
        # No decision indicators found
        if priority is None:
            return None
        
        # Determine category if not set
        if category == 'general':
            category = self._determine_category(sentence_lower)
        
        # Boost confidence for specific patterns
        if 'agreed to remove' in sentence_lower or 'decided to remove' in sentence_lower:
            priority = 'high'
            confidence = 0.95
        
        if 'on-call' in sentence_lower and any(word in sentence_lower for word in ['remove', 'eliminate', 'change']):
            priority = 'high'
            confidence = 0.95
            category = 'process'
        
        return {
            'decision': sentence.strip(),
            'priority': priority,
            'category': category,
            'confidence': confidence
        }
    
    def _determine_category(self, sentence: str) -> str:
        """Determine decision category from content"""
        for category, keywords in self.engineering_keywords.items():
            if any(keyword in sentence for keyword in keywords):
                return category
        
        return 'general'
    
    def filter_by_confidence(self, decisions: List[Dict], min_confidence: float = 0.7) -> List[Dict]:
        """Filter decisions by minimum confidence"""
        return [d for d in decisions if d['confidence'] >= min_confidence]
    
    def format_for_output(self, decisions: List[Dict]) -> List[str]:
        """Format decisions for output (array of strings)"""
        return [d['decision'] for d in decisions]


# Example usage
if __name__ == "__main__":
    classifier = DecisionClassifier()
    
    # Test with sample transcript
    transcript = """
    The team discussed various topics. We decided to iterate on the infrared dev escalation process.
    Everyone agreed to remove the weekend on-call rotation due to legal concerns.
    We should probably consider hiring more engineers in Q4.
    The team will implement T-shirt sizing on all issues starting next week.
    Maybe we could look into using PostgreSQL instead of MySQL.
    """
    
    print("="*70)
    print("DECISION CLASSIFICATION TEST")
    print("="*70)
    
    decisions = classifier.extract_decisions(transcript)
    
    print(f"\nFound {len(decisions)} decisions:\n")
    
    for i, decision in enumerate(decisions, 1):
        print(f"{i}. [{decision['priority'].upper()}] {decision['decision']}")
        print(f"   Category: {decision['category']}")
        print(f"   Confidence: {decision['confidence']:.2f}")
        print()
    
    # Filter high confidence
    high_conf = classifier.filter_by_confidence(decisions, min_confidence=0.8)
    
    print(f"\nHigh confidence decisions ({len(high_conf)}):")
    for decision in high_conf:
        print(f"  - {decision['decision']}")
    
    # Format for output
    formatted = classifier.format_for_output(high_conf)
    
    print(f"\nFormatted output:")
    print(formatted)
