"""
Meeting Type Detector
Identifies meeting type and adjusts analysis accordingly
"""
import re
from typing import Dict, List

class MeetingTypeDetector:
    """
    Detect meeting type and provide context-specific analysis rules
    
    Meeting Types:
    - formal: Council, government, board meetings
    - technical: Engineering, development meetings
    - business: Corporate, sales, strategy meetings
    - casual: Team standups, informal discussions
    """
    
    def __init__(self):
        # Meeting type indicators
        self.formal_indicators = {
            'keywords': [
                'council', 'councillor', 'motion', 'agenda', 'delegation',
                'call to order', 'adoption', 'mayor', 'board', 'committee',
                'resolution', 'vote', 'minutes', 'quorum', 'adjourn'
            ],
            'roles': [
                'councillor', 'mayor', 'chair', 'secretary', 'clerk',
                'commissioner', 'board member', 'trustee'
            ],
            'procedures': [
                'moved', 'seconded', 'carried', 'defeated', 'tabled',
                'referred', 'amended', 'withdrawn'
            ]
        }
        
        self.technical_indicators = {
            'keywords': [
                'infrared dev', 'on-call', 'escalation', 'deployment',
                'api', 'database', 'architecture', 'code review',
                'sprint', 'backlog', 'merge request', 'pull request'
            ],
            'roles': [
                'engineer', 'developer', 'architect', 'tech lead',
                'product manager', 'scrum master'
            ]
        }
        
        self.business_indicators = {
            'keywords': [
                'revenue', 'sales', 'marketing', 'strategy', 'budget',
                'forecast', 'roi', 'kpi', 'metrics', 'quarterly'
            ],
            'roles': [
                'ceo', 'cfo', 'vp', 'director', 'manager', 'executive'
            ]
        }
    
    def detect_meeting_type(self, transcript: str, title: str = "") -> Dict:
        """
        Detect meeting type from transcript and title
        
        Returns:
            {
                'type': 'formal' | 'technical' | 'business' | 'casual',
                'confidence': 0.0-1.0,
                'indicators': [...],
                'analysis_rules': {...}
            }
        """
        transcript_lower = transcript.lower()
        title_lower = title.lower()
        combined = transcript_lower + " " + title_lower
        
        # Count indicators for each type
        formal_score = self._calculate_score(combined, self.formal_indicators)
        technical_score = self._calculate_score(combined, self.technical_indicators)
        business_score = self._calculate_score(combined, self.business_indicators)
        
        # Determine type
        scores = {
            'formal': formal_score,
            'technical': technical_score,
            'business': business_score,
            'casual': 0.1  # Default baseline
        }
        
        meeting_type = max(scores, key=scores.get)
        confidence = scores[meeting_type]
        
        # Get analysis rules for this type
        analysis_rules = self._get_analysis_rules(meeting_type)
        
        # Get indicators found
        indicators = self._get_indicators_found(combined, meeting_type)
        
        return {
            'type': meeting_type,
            'confidence': min(confidence, 1.0),
            'indicators': indicators,
            'analysis_rules': analysis_rules
        }
    
    def _calculate_score(self, text: str, indicators: Dict) -> float:
        """Calculate score for meeting type"""
        score = 0.0
        
        # Check keywords
        for keyword in indicators.get('keywords', []):
            if keyword in text:
                score += 0.1
        
        # Check roles
        for role in indicators.get('roles', []):
            if role in text:
                score += 0.15
        
        # Check procedures (formal only)
        for procedure in indicators.get('procedures', []):
            if procedure in text:
                score += 0.2
        
        return score
    
    def _get_indicators_found(self, text: str, meeting_type: str) -> List[str]:
        """Get list of indicators found"""
        indicators = []
        
        if meeting_type == 'formal':
            source = self.formal_indicators
        elif meeting_type == 'technical':
            source = self.technical_indicators
        elif meeting_type == 'business':
            source = self.business_indicators
        else:
            return []
        
        for category in source.values():
            for indicator in category:
                if indicator in text:
                    indicators.append(indicator)
        
        return indicators[:10]  # Limit to 10
    
    def _get_analysis_rules(self, meeting_type: str) -> Dict:
        """Get analysis rules for meeting type"""
        
        if meeting_type == 'formal':
            return {
                'decision_filter': 'policy_only',  # Ignore procedural
                'decision_types': [
                    'policy_change',
                    'budget_approval',
                    'operational_decision',
                    'public_concern_response',
                    'resource_allocation'
                ],
                'ignore_decisions': [
                    'call to order',
                    'adoption of agenda',
                    'moved and seconded',
                    'meeting adjourned',
                    'item moved to'
                ],
                'extract_entities': [
                    'locations',
                    'public_concerns',
                    'policy_areas',
                    'budget_items'
                ],
                'action_item_rules': {
                    'require_explicit_owner': False,
                    'mark_suggested_actions': True,
                    'extract_follow_ups': True
                }
            }
        
        elif meeting_type == 'technical':
            return {
                'decision_filter': 'technical_only',
                'decision_types': [
                    'architecture_decision',
                    'technology_choice',
                    'process_change',
                    'deployment_decision'
                ],
                'ignore_decisions': [],
                'extract_entities': [
                    'technologies',
                    'systems',
                    'processes'
                ],
                'action_item_rules': {
                    'require_explicit_owner': True,
                    'mark_suggested_actions': False,
                    'extract_follow_ups': True
                }
            }
        
        elif meeting_type == 'business':
            return {
                'decision_filter': 'strategic_only',
                'decision_types': [
                    'strategic_decision',
                    'budget_decision',
                    'hiring_decision',
                    'partnership_decision'
                ],
                'ignore_decisions': [],
                'extract_entities': [
                    'companies',
                    'products',
                    'markets',
                    'financials'
                ],
                'action_item_rules': {
                    'require_explicit_owner': True,
                    'mark_suggested_actions': False,
                    'extract_follow_ups': True
                }
            }
        
        else:  # casual
            return {
                'decision_filter': 'all',
                'decision_types': ['any'],
                'ignore_decisions': [],
                'extract_entities': [],
                'action_item_rules': {
                    'require_explicit_owner': False,
                    'mark_suggested_actions': True,
                    'extract_follow_ups': True
                }
            }
    
    def filter_procedural_decisions(self, decisions: List[str], meeting_type: str) -> List[str]:
        """Filter out procedural decisions for formal meetings"""
        
        if meeting_type != 'formal':
            return decisions
        
        rules = self._get_analysis_rules(meeting_type)
        ignore_patterns = rules['ignore_decisions']
        
        filtered = []
        
        for decision in decisions:
            decision_lower = decision.lower()
            
            # Check if it matches any ignore pattern
            is_procedural = any(pattern in decision_lower for pattern in ignore_patterns)
            
            if not is_procedural:
                filtered.append(decision)
            else:
                print(f"🗑️  Filtered procedural: '{decision}'")
        
        return filtered
    
    def classify_action_items(self, action_items: List[Dict], meeting_type: str) -> List[Dict]:
        """Classify action items based on meeting type"""
        
        rules = self._get_analysis_rules(meeting_type)
        action_rules = rules['action_item_rules']
        
        classified = []
        
        for item in action_items:
            owner = item.get('owner', '')
            
            # Mark as suggested if no explicit owner
            if not owner and action_rules['mark_suggested_actions']:
                item['type'] = 'suggested'
            else:
                item['type'] = 'assigned'
            
            classified.append(item)
        
        return classified


# Example usage
if __name__ == "__main__":
    detector = MeetingTypeDetector()
    
    # Test with formal meeting
    formal_transcript = """
    Councillor Palatje moved to adopt the agenda, seconded by Councillor Belanchet.
    The motion was carried. Staff Sergeant Ron Poydor presented statistics.
    Council discussed safety concerns on Bernat road.
    """
    
    print("="*70)
    print("MEETING TYPE DETECTION TEST")
    print("="*70)
    
    result = detector.detect_meeting_type(formal_transcript, "Council Meeting")
    
    print(f"\nMeeting Type: {result['type']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"\nIndicators found:")
    for indicator in result['indicators']:
        print(f"  - {indicator}")
    
    print(f"\nAnalysis Rules:")
    print(f"  Decision Filter: {result['analysis_rules']['decision_filter']}")
    print(f"  Ignore Decisions: {result['analysis_rules']['ignore_decisions']}")
    
    # Test decision filtering
    print("\n" + "="*70)
    print("DECISION FILTERING TEST")
    print("="*70)
    
    decisions = [
        "Move item 7.1 to next on agenda",
        "Adoption of the agenda",
        "Increase police presence on Bernat road",
        "Fill vacancy on provincial side"
    ]
    
    print("\nOriginal decisions:")
    for d in decisions:
        print(f"  - {d}")
    
    filtered = detector.filter_procedural_decisions(decisions, 'formal')
    
    print("\nFiltered decisions (procedural removed):")
    for d in filtered:
        print(f"  ✅ {d}")
