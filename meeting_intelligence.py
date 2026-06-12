"""
Consolidated Meeting Intelligence Module
Combines: meeting_type_detector, formal_meeting_detector, formal_meeting_extractor, entity_extractor
"""
from typing import Dict, List, Tuple
import re

# ============================================
# MEETING TYPE DETECTOR
# ============================================

class MeetingTypeDetector:
    """Detects meeting type for context-aware analysis"""
    
    def __init__(self):
        self.meeting_types = {
            'formal': {
                'keywords': ['council', 'board', 'committee', 'motion', 'agenda', 'minutes', 'vote', 'resolution'],
                'patterns': [r'\bmotion\s+(?:to|for)', r'\bagenda\s+item', r'\bvote\s+on', r'\bminutes\s+of']
            },
            'technical': {
                'keywords': ['deployment', 'infrastructure', 'code', 'bug', 'feature', 'sprint', 'api', 'database'],
                'patterns': [r'\bon-call', r'\bMR\b', r'\bPR\b', r'\bCI/CD', r'\bGitOps']
            },
            'business': {
                'keywords': ['revenue', 'sales', 'marketing', 'strategy', 'quarter', 'budget', 'roi', 'kpi'],
                'patterns': [r'\bQ[1-4]\b', r'\bARR\b', r'\bMRR\b', r'\bGTM\b']
            },
            'casual': {
                'keywords': ['standup', 'sync', 'catch-up', 'check-in', 'update', 'quick'],
                'patterns': [r'\bstand\s*up', r'\bcheck\s*in']
            }
        }
    
    def detect_meeting_type(self, transcript: str, title: str = "") -> Dict:
        """Detect meeting type from transcript and title"""
        combined_text = f"{title} {transcript}".lower()
        
        scores = {}
        indicators = {}
        
        for meeting_type, config in self.meeting_types.items():
            score = 0
            found_indicators = []
            
            for keyword in config['keywords']:
                if keyword in combined_text:
                    score += 1
                    found_indicators.append(keyword)
            
            for pattern in config['patterns']:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    score += 2
                    found_indicators.append(pattern)
            
            scores[meeting_type] = score
            indicators[meeting_type] = found_indicators
        
        detected_type = max(scores, key=scores.get)
        max_score = scores[detected_type]
        
        if max_score == 0:
            detected_type = 'casual'
            confidence = 0.5
        else:
            total_score = sum(scores.values())
            confidence = max_score / total_score if total_score > 0 else 0.5
        
        return {
            'type': detected_type,
            'confidence': confidence,
            'scores': scores,
            'indicators': indicators[detected_type],
            'analysis_rules': self._get_analysis_rules(detected_type)
        }
    
    def _get_analysis_rules(self, meeting_type: str) -> Dict:
        """Get analysis rules for meeting type"""
        rules = {
            'formal': {
                'filter_procedural': True,
                'extract_entities': True,
                'require_explicit_decisions': True
            },
            'technical': {
                'understand_terminology': True,
                'track_technical_decisions': True,
                'require_owners': True
            },
            'business': {
                'track_metrics': True,
                'understand_business_terms': True,
                'track_goals': True
            },
            'casual': {
                'flexible_language': True,
                'informal_decisions': True
            }
        }
        
        return rules.get(meeting_type, {})
    
    def filter_procedural_decisions(self, decisions: List[str], meeting_type: str) -> List[str]:
        """Filter out procedural decisions for formal meetings"""
        if meeting_type != 'formal':
            return decisions
        
        procedural_patterns = [
            r'call\s+to\s+order',
            r'adoption\s+of\s+agenda',
            r'moved\s+and\s+seconded',
            r'meeting\s+adjourned',
            r'item\s+moved\s+to',
            r'agenda\s+item\s+\d+'
        ]
        
        filtered = []
        for decision in decisions:
            is_procedural = any(re.search(pattern, decision, re.IGNORECASE) for pattern in procedural_patterns)
            if not is_procedural:
                filtered.append(decision)
        
        return filtered
    
    def classify_action_items(self, action_items: List[Dict], meeting_type: str) -> List[Dict]:
        """Classify action items based on meeting type"""
        if meeting_type != 'formal':
            return action_items
        
        for item in action_items:
            if not item.get('owner'):
                item['type'] = 'suggested'
            else:
                item['type'] = 'assigned'
        
        return action_items


# ============================================
# FORMAL MEETING EXTRACTOR
# ============================================

class FormalMeetingExtractor:
    """Specialized extraction for formal/government meetings"""
    
    def __init__(self):
        self.location_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:road|street|avenue|drive|lane|boulevard)',
            r'\b(?:at|on|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        self.concern_patterns = [
            r'concern\s+(?:about|regarding|over)\s+([^.]+)',
            r'issue\s+(?:with|about|regarding)\s+([^.]+)',
            r'problem\s+(?:with|at|on)\s+([^.]+)',
        ]
        
        self.official_patterns = [
            r'(?:Mayor|Councillor|Chair|Director|Chief)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        ]
    
    def extract_formal_entities(self, transcript: str) -> Dict:
        """Extract entities specific to formal meetings"""
        entities = {
            'locations': [],
            'concerns': [],
            'officials': []
        }
        
        for pattern in self.location_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            entities['locations'].extend(matches)
        
        for pattern in self.concern_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            entities['concerns'].extend([m.strip() for m in matches])
        
        for pattern in self.official_patterns:
            matches = re.findall(pattern, transcript)
            entities['officials'].extend(matches)
        
        entities['locations'] = list(set(entities['locations']))
        entities['concerns'] = list(set(entities['concerns']))
        entities['officials'] = list(set(entities['officials']))
        
        return entities


# ============================================
# ENTITY EXTRACTOR
# ============================================

class EntityExtractor:
    """Extract key entities from transcript"""
    
    def __init__(self):
        self.nlp = None
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except:
            print("⚠️  spaCy not available, using regex-based NER")
            print("💡 Install: python -m spacy download en_core_web_sm")
    
    def extract_key_entities(self, transcript: str) -> Dict:
        """Extract people, organizations, dates, money from transcript"""
        if self.nlp:
            return self._extract_with_spacy(transcript)
        else:
            return self._extract_with_regex(transcript)
    
    def _extract_with_spacy(self, transcript: str) -> Dict:
        """Extract entities using spaCy"""
        doc = self.nlp(transcript)
        
        entities = {
            'people': [],
            'organizations': [],
            'dates': [],
            'money': [],
            'locations': []
        }
        
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                entities['people'].append(ent.text)
            elif ent.label_ == 'ORG':
                entities['organizations'].append(ent.text)
            elif ent.label_ == 'DATE':
                entities['dates'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entities['money'].append(ent.text)
            elif ent.label_ in ['GPE', 'LOC']:
                entities['locations'].append(ent.text)
        
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def _extract_with_regex(self, transcript: str) -> Dict:
        """Fallback: Extract entities using regex"""
        entities = {
            'people': [],
            'organizations': [],
            'dates': [],
            'money': [],
            'locations': []
        }
        
        name_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
        names = re.findall(name_pattern, transcript)
        entities['people'] = list(set(names))
        
        date_patterns = [
            r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}',
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\bQ[1-4]\s+\d{4}\b'
        ]
        
        for pattern in date_patterns:
            dates = re.findall(pattern, transcript, re.IGNORECASE)
            entities['dates'].extend(dates)
        
        money_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?(?:\s*(?:million|billion|thousand|k|m|b))?'
        money = re.findall(money_pattern, transcript, re.IGNORECASE)
        entities['money'] = list(set(money))
        
        entities['dates'] = list(set(entities['dates']))
        
        return entities
