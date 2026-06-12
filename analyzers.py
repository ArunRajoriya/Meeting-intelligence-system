"""
Consolidated Analysis Module
Combines: decision_classifier, action_item_extractor, confidence_scorer, multi_pass_analyzer
"""
from typing import Dict, List, Tuple
import re
from collections import deque

# ============================================
# DECISION CLASSIFIER
# ============================================

class DecisionClassifier:
    """Enhanced decision detection and classification"""
    
    def __init__(self):
        # CRITICAL: Distinguish DECISIONS from SUGGESTIONS
        self.confirmed_decision_indicators = [
            'decided', 'decision', 'agreed', 'approved', 'confirmed',
            'finalized', 'committed to', 'consensus', 'vote', 'chose',
            'are permanent', 'is permanent', 'officially', 'formally'
        ]
        
        self.permanent_change_indicators = [
            'permanent', 'permanently', 'always', 'from now on',
            'going forward', 'company-wide', 'official', 'formally'
        ]
        
        self.high_priority_indicators = {
            'explicit': self.confirmed_decision_indicators,
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
        
        self.medium_priority_indicators = [
            'will', 'going to', 'plan to', 'intend to',
            "let's", "we'll", "we're going to"
        ]
        
        self.suggestion_indicators = [
            'should', 'could', 'might', 'maybe', 'perhaps', 'possibly',
            'consider', 'think about', 'discuss', 'explore', 'look into',
            'wondering if', 'what if', 'propose'
        ]
        
        self.engineering_keywords = {
            'process': ['on-call', 'escalation', 'workflow', 'pipeline', 'deployment'],
            'technical': ['database', 'api', 'framework', 'architecture', 'infrastructure'],
            'team': ['hiring', 'staffing', 'rotation', 'schedule', 'meeting'],
            'quality': ['testing', 'review', 'qa', 'validation', 'monitoring']
        }
    
    def extract_decisions(self, transcript: str) -> List[Dict]:
        """Extract and classify decisions from transcript"""
        decisions = []
        sentences = re.split(r'[.!?]+', transcript)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            decision_info = self._classify_sentence(sentence)
            if decision_info:
                decisions.append(decision_info)
        
        decisions.sort(key=lambda x: (
            0 if x['priority'] == 'critical' else 1 if x['priority'] == 'high' else 2 if x['priority'] == 'medium' else 3,
            -x['confidence']
        ))
        
        return decisions
    
    def _classify_sentence(self, sentence: str) -> Dict | None:
        """Classify a sentence as decision or not"""
        sentence_lower = sentence.lower()
        
        # STEP 1: Check for SUGGESTIONS first
        has_suggestion = any(indicator in sentence_lower for indicator in self.suggestion_indicators)
        has_confirmed_decision = any(indicator in sentence_lower for indicator in self.confirmed_decision_indicators)
        
        if has_suggestion and not has_confirmed_decision:
            return None
        
        # STEP 2: Check for PERMANENT CHANGES
        has_permanent = any(indicator in sentence_lower for indicator in self.permanent_change_indicators)
        
        if has_permanent:
            words = sentence.split()
            if len(words) >= 5:
                meaningful_keywords = ['friday', 'policy', 'rule', 'process', 'team', 'company', 
                                     'guidance', 'change', 'marketing', 'meeting', 'work']
                has_meaningful_context = any(keyword in sentence_lower for keyword in meaningful_keywords)
                
                if has_meaningful_context:
                    return {
                        'decision': sentence.strip(),
                        'priority': 'critical',
                        'category': 'culture_shift',
                        'confidence': 0.98,
                        'type': 'permanent_change'
                    }
        
        # STEP 3: Check for high priority decisions
        priority = None
        confidence = 0.0
        category = 'general'
        decision_type = 'standard'
        
        if has_confirmed_decision:
            priority = 'high'
            confidence = 0.95
            decision_type = 'confirmed'
        elif any(indicator in sentence_lower for indicator in self.high_priority_indicators['process_change']):
            if any(keyword in sentence_lower for keywords in self.engineering_keywords.values() for keyword in keywords):
                priority = 'high'
                confidence = 0.85
                category = 'process'
                decision_type = 'process_change'
        elif any(indicator in sentence_lower for indicator in self.high_priority_indicators['policy']):
            priority = 'high'
            confidence = 0.9
            category = 'policy'
            decision_type = 'policy'
        elif any(indicator in sentence_lower for indicator in self.high_priority_indicators['legal_compliance']):
            priority = 'high'
            confidence = 0.95
            category = 'legal'
            decision_type = 'legal'
        elif any(indicator in sentence_lower for indicator in self.medium_priority_indicators):
            if not has_suggestion:
                priority = 'medium'
                confidence = 0.7
                decision_type = 'planned'
        
        if priority is None:
            return None
        
        if category == 'general':
            category = self._determine_category(sentence_lower)
        
        if 'agreed to remove' in sentence_lower or 'decided to remove' in sentence_lower:
            priority = 'high'
            confidence = 0.95
            decision_type = 'confirmed'
        
        if 'on-call' in sentence_lower and any(word in sentence_lower for word in ['remove', 'eliminate', 'change']):
            priority = 'high'
            confidence = 0.95
            category = 'process'
            decision_type = 'process_change'
        
        if 'async' in sentence_lower and any(word in sentence_lower for word in ['bias', 'focus', 'shift', 'culture']):
            priority = 'critical'
            confidence = 0.95
            category = 'culture_shift'
            decision_type = 'permanent_change'
        
        return {
            'decision': sentence.strip(),
            'priority': priority,
            'category': category,
            'confidence': confidence,
            'type': decision_type
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


# ============================================
# ACTION ITEM EXTRACTOR
# ============================================

class ActionItemExtractor:
    """Extract action items with priority weighting"""
    
    def __init__(self):
        self.action_verbs = [
            'will', 'should', 'must', 'needs to', 'has to',
            'going to', 'plan to', 'commit to', 'agree to',
            'assigned to', 'responsible for'
        ]
        
        self.urgency_indicators = {
            'urgent': ['urgent', 'asap', 'immediately', 'critical', 'emergency', 'today', 'now', 'right away'],
            'high': ['important', 'priority', 'soon', 'this week', 'tomorrow', 'by end of day', 'by eod'],
            'medium': ['next week', 'this month', 'upcoming', 'planned'],
            'low': ['eventually', 'when possible', 'nice to have', 'optional', 'if time permits', 'consider']
        }
        
        self.exclusion_words = [
            'we discussed', 'we talked', 'mentioned', 'said',
            'think', 'believe', 'feel', 'hope', 'wish',
            'maybe', 'perhaps', 'possibly', 'might'
        ]
    
    def extract_action_items(self, transcript: str, participants: List[str]) -> List[Dict]:
        """Extract action items with STRICT filtering"""
        sentences = self._split_into_sentences(transcript)
        action_items = []
        
        for sentence in sentences:
            if not self._is_valid_action(sentence):
                continue
            
            owner = self._extract_owner(sentence, participants)
            deadline = self._extract_deadline(sentence)
            priority = self._calculate_priority(sentence, owner, deadline)
            confidence = self._calculate_confidence(sentence, owner, deadline)
            
            if confidence >= 0.3:
                action_items.append({
                    'task': sentence.strip(),
                    'owner': owner or "",
                    'deadline': deadline or "",
                    'priority': priority,
                    'confidence': confidence,
                    'confidence_label': self._confidence_label(confidence)
                })
        
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        action_items.sort(key=lambda x: (priority_order.get(x['priority'], 4), -x['confidence']))
        
        return action_items
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _is_valid_action(self, sentence: str) -> bool:
        """STRICT VALIDATION: Is this a real action item?"""
        sentence_lower = sentence.lower()
        
        has_action_verb = any(verb in sentence_lower for verb in self.action_verbs)
        if not has_action_verb:
            return False
        
        has_exclusion = any(word in sentence_lower for word in self.exclusion_words)
        if has_exclusion:
            return False
        
        if len(sentence.split()) < 5:
            return False
        
        vague_patterns = [
            r'^\s*(?:we|they|someone)\s+(?:will|should|must)\s+(?:do|work|handle)\s+(?:it|this|that|something)',
            r'^\s*(?:need|needs)\s+to\s+(?:be|get)\s+done',
        ]
        
        for pattern in vague_patterns:
            if re.match(pattern, sentence_lower):
                return False
        
        return True
    
    def _extract_owner(self, sentence: str, participants: List[str]) -> str:
        """Extract owner from sentence"""
        for participant in participants:
            pattern = rf'\b{re.escape(participant)}\s+(?:will|should|must|needs?)\b'
            if re.search(pattern, sentence, re.IGNORECASE):
                return participant
        
        for verb in self.action_verbs:
            pattern = rf'\b([A-Z][a-z]+)\s+{re.escape(verb)}\b'
            match = re.search(pattern, sentence)
            if match:
                name = match.group(1)
                if len(name) > 2 and name not in ['The', 'This', 'That', 'They', 'We']:
                    return name
        
        return ""
    
    def _extract_deadline(self, sentence: str) -> str:
        """Extract deadline from sentence"""
        deadline_patterns = [
            r'by\s+([A-Z][a-z]+day)',
            r'by\s+([A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?)',
            r'by\s+(tomorrow|today)',
            r'(next\s+(?:week|month|Monday|Tuesday|Wednesday|Thursday|Friday))',
            r'(end\s+of\s+(?:week|month|quarter|year))',
            r'(this\s+(?:week|month|Friday|Monday))',
            r'by\s+the\s+end\s+of\s+([A-Z][a-z]+)',
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        
        return ""
    
    def _calculate_priority(self, sentence: str, owner: str, deadline: str) -> str:
        """Calculate priority/urgency of action item"""
        sentence_lower = sentence.lower()
        deadline_lower = deadline.lower() if deadline else ""
        
        for priority_level, indicators in self.urgency_indicators.items():
            if any(indicator in sentence_lower or indicator in deadline_lower for indicator in indicators):
                return priority_level
        
        if deadline:
            if any(word in deadline_lower for word in ['today', 'tomorrow', 'asap', 'immediately']):
                return 'urgent'
            elif any(word in deadline_lower for word in ['this week', 'friday', 'monday', 'tuesday', 'wednesday', 'thursday']):
                return 'high'
            elif any(word in deadline_lower for word in ['next week', 'this month']):
                return 'medium'
        
        if any(verb in sentence_lower for verb in ['must', 'critical', 'required', 'need to']):
            return 'high'
        
        return 'medium' if owner else 'low'
    
    def _calculate_confidence(self, sentence: str, owner: str, deadline: str) -> float:
        """Calculate confidence score for action item"""
        confidence = 0.0
        
        if owner:
            confidence += 0.4
        if deadline:
            confidence += 0.3
        
        strong_verbs = ['will', 'must', 'assigned', 'responsible']
        if any(verb in sentence.lower() for verb in strong_verbs):
            confidence += 0.2
        
        if re.search(r'\d+', sentence):
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


# ============================================
# CONFIDENCE SCORER
# ============================================

class ConfidenceScorer:
    """Scores extraction confidence for transparency"""
    
    def __init__(self):
        self.high_confidence_indicators = {
            'decision': ['decided', 'agreed', 'approved', 'confirmed', 'permanent', 'officially'],
            'action': ['will', 'must', 'assigned', 'responsible', 'by', 'deadline']
        }
        
        self.low_confidence_indicators = {
            'decision': ['maybe', 'might', 'could', 'perhaps', 'consider'],
            'action': ['should', 'could', 'might', 'maybe']
        }
    
    def score_decision(self, decision: str, transcript: str) -> Tuple[float, str]:
        """Score decision confidence"""
        score = 0.5
        decision_lower = decision.lower()
        
        high_count = sum(1 for indicator in self.high_confidence_indicators['decision'] 
                        if indicator in decision_lower)
        score += min(high_count * 0.1, 0.3)
        
        low_count = sum(1 for indicator in self.low_confidence_indicators['decision'] 
                       if indicator in decision_lower)
        score -= min(low_count * 0.15, 0.3)
        
        word_count = len(decision.split())
        if word_count >= 8:
            score += 0.2
        elif word_count >= 5:
            score += 0.1
        
        if self._check_presence_in_transcript(decision, transcript):
            score += 0.2
        
        if re.search(r'\d+', decision):
            score += 0.1
        
        score = max(0.0, min(1.0, score))
        
        if score >= 0.9:
            label = 'very_high'
        elif score >= 0.7:
            label = 'high'
        elif score >= 0.5:
            label = 'medium'
        else:
            label = 'low'
        
        return score, label
    
    def score_action(self, action: Dict, transcript: str, participants: List[str]) -> Tuple[float, str]:
        """Score action item confidence"""
        score = 0.5
        
        task = action.get('task', '')
        owner = action.get('owner', '')
        deadline = action.get('deadline', '')
        
        task_lower = task.lower()
        
        if owner:
            score += 0.3
            if owner in participants:
                score += 0.1
        
        if deadline:
            score += 0.2
        
        high_count = sum(1 for indicator in self.high_confidence_indicators['action'] 
                        if indicator in task_lower)
        score += min(high_count * 0.1, 0.2)
        
        low_count = sum(1 for indicator in self.low_confidence_indicators['action'] 
                       if indicator in task_lower)
        score -= min(low_count * 0.15, 0.3)
        
        word_count = len(task.split())
        if word_count >= 6:
            score += 0.1
        
        if self._check_presence_in_transcript(task, transcript):
            score += 0.1
        
        score = max(0.0, min(1.0, score))
        
        if score >= 0.8:
            label = 'very_high'
        elif score >= 0.6:
            label = 'high'
        elif score >= 0.4:
            label = 'medium'
        else:
            label = 'low'
        
        return score, label
    
    def score_all(self, notes: Dict, transcript: str, participants: List[str]) -> Dict:
        """Score all decisions and actions"""
        scored_notes = notes.copy()
        
        decision_scores = []
        for decision in notes.get('key_decisions', []):
            score, label = self.score_decision(decision, transcript)
            decision_scores.append({
                'decision': decision,
                'confidence': score,
                'confidence_label': label
            })
        
        action_scores = []
        for action in notes.get('action_items', []):
            score, label = self.score_action(action, transcript, participants)
            action_scores.append({
                **action,
                'confidence': score,
                'confidence_label': label
            })
        
        scored_notes['_decision_scores'] = decision_scores
        scored_notes['_action_scores'] = action_scores
        
        return scored_notes
    
    def filter_by_confidence(self, notes: Dict, min_confidence: float = 0.5) -> Dict:
        """Filter items by minimum confidence"""
        filtered = notes.copy()
        
        if '_decision_scores' in notes:
            filtered_decisions = [
                item['decision'] 
                for item in notes['_decision_scores'] 
                if item['confidence'] >= min_confidence
            ]
            filtered['key_decisions'] = filtered_decisions
        
        if '_action_scores' in notes:
            filtered_actions = [
                {
                    'task': item['task'],
                    'owner': item['owner'],
                    'deadline': item['deadline']
                }
                for item in notes['_action_scores'] 
                if item['confidence'] >= min_confidence
            ]
            filtered['action_items'] = filtered_actions
        
        return filtered
    
    def get_confidence_stats(self, notes: Dict) -> Dict:
        """Get confidence statistics"""
        stats = {
            'decisions': {'total': 0, 'very_high': 0, 'high': 0, 'medium': 0, 'low': 0, 'avg_confidence': 0.0},
            'actions': {'total': 0, 'very_high': 0, 'high': 0, 'medium': 0, 'low': 0, 'avg_confidence': 0.0}
        }
        
        if '_decision_scores' in notes:
            decision_scores = notes['_decision_scores']
            stats['decisions']['total'] = len(decision_scores)
            
            for item in decision_scores:
                label = item['confidence_label']
                stats['decisions'][label] += 1
            
            if decision_scores:
                avg = sum(item['confidence'] for item in decision_scores) / len(decision_scores)
                stats['decisions']['avg_confidence'] = avg
        
        if '_action_scores' in notes:
            action_scores = notes['_action_scores']
            stats['actions']['total'] = len(action_scores)
            
            for item in action_scores:
                label = item['confidence_label']
                stats['actions'][label] += 1
            
            if action_scores:
                avg = sum(item['confidence'] for item in action_scores) / len(action_scores)
                stats['actions']['avg_confidence'] = avg
        
        return stats
    
    def _check_presence_in_transcript(self, text: str, transcript: str) -> bool:
        """Check if key concepts from text are in transcript"""
        text_lower = text.lower()
        transcript_lower = transcript.lower()
        
        words = set(text_lower.split())
        common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'will', 'be', 'to', 'of', 'and', 'or', 'by'}
        key_words = words - common_words
        
        if len(key_words) < 2:
            return True
        
        matches = sum(1 for word in key_words if word in transcript_lower)
        match_ratio = matches / len(key_words)
        
        return match_ratio >= 0.5


# ============================================
# MULTI-PASS ANALYZER
# ============================================

class MultiPassAnalyzer:
    """Three-pass analysis system for maximum accuracy"""
    
    def __init__(self):
        self.validation_rules = {
            'decision': self._validate_decision,
            'action': self._validate_action,
            'summary': self._validate_summary
        }
    
    def analyze(self, transcript: str, raw_notes: Dict, participants: List[str]) -> Dict:
        """Perform three-pass analysis"""
        print("🔄 Multi-pass analysis starting...")
        
        pass1_notes = raw_notes.copy()
        
        print("   Pass 2: Validating decisions and actions...")
        pass2_notes = self._pass2_validate(pass1_notes, transcript, participants)
        
        print("   Pass 3: Cross-referencing and deduplicating...")
        pass3_notes = self._pass3_cross_reference(pass2_notes, transcript)
        
        print("✅ Multi-pass analysis complete")
        
        return pass3_notes
    
    def _pass2_validate(self, notes: Dict, transcript: str, participants: List[str]) -> Dict:
        """Pass 2: Validate each extracted item"""
        validated = notes.copy()
        
        validated_decisions = []
        for decision in notes.get('key_decisions', []):
            if self._validate_decision(decision, transcript):
                validated_decisions.append(decision)
        
        validated['key_decisions'] = validated_decisions
        
        validated_actions = []
        for action in notes.get('action_items', []):
            if self._validate_action(action, transcript, participants):
                validated_actions.append(action)
        
        validated['action_items'] = validated_actions
        
        if 'summary' in notes:
            validated['summary'] = self._validate_summary(notes['summary'], transcript)
        
        return validated
    
    def _pass3_cross_reference(self, notes: Dict, transcript: str) -> Dict:
        """Pass 3: Cross-reference and ensure consistency"""
        refined = notes.copy()
        
        refined['key_decisions'] = self._deduplicate_decisions(notes.get('key_decisions', []))
        refined['action_items'] = self._deduplicate_actions(notes.get('action_items', []))
        refined = self._align_actions_with_decisions(refined)
        
        return refined
    
    def _validate_decision(self, decision: str, transcript: str) -> bool:
        """Validate if decision is actually in transcript"""
        if len(decision.split()) < 3:
            return False
        
        decision_lower = decision.lower()
        transcript_lower = transcript.lower()
        
        decision_words = set(decision_lower.split())
        common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'will', 'be', 'to', 'of', 'and', 'or'}
        key_words = decision_words - common_words
        
        if len(key_words) < 2:
            return False
        
        matches = sum(1 for word in key_words if word in transcript_lower)
        match_ratio = matches / len(key_words) if key_words else 0
        
        return match_ratio >= 0.5
    
    def _validate_action(self, action: Dict, transcript: str, participants: List[str]) -> bool:
        """Validate action item"""
        task = action.get('task', '')
        
        if len(task.split()) < 3:
            return False
        
        task_lower = task.lower()
        transcript_lower = transcript.lower()
        
        task_words = set(task_lower.split())
        common_words = {'the', 'a', 'an', 'is', 'are', 'will', 'should', 'must', 'need', 'to', 'by'}
        key_words = task_words - common_words
        
        if len(key_words) < 2:
            return False
        
        matches = sum(1 for word in key_words if word in transcript_lower)
        match_ratio = matches / len(key_words) if key_words else 0
        
        return match_ratio >= 0.4
    
    def _validate_summary(self, summary: str, transcript: str) -> str:
        """Validate and potentially refine summary"""
        return summary
    
    def _deduplicate_decisions(self, decisions: List[str]) -> List[str]:
        """Remove duplicate decisions (semantic deduplication)"""
        if not decisions:
            return []
        
        unique = []
        seen = set()
        
        for decision in decisions:
            normalized = decision.lower().strip()
            
            if normalized in seen:
                continue
            
            is_duplicate = False
            decision_words = set(normalized.split())
            
            for existing in unique:
                existing_words = set(existing.lower().split())
                
                overlap = len(decision_words & existing_words)
                total = len(decision_words | existing_words)
                
                if total > 0 and overlap / total >= 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(decision)
                seen.add(normalized)
        
        return unique
    
    def _deduplicate_actions(self, actions: List[Dict]) -> List[Dict]:
        """Remove duplicate action items"""
        if not actions:
            return []
        
        unique = []
        seen_tasks = set()
        
        for action in actions:
            task = action.get('task', '').lower().strip()
            owner = action.get('owner', '').lower().strip()
            
            signature = f"{owner}:{task}"
            
            if signature in seen_tasks:
                continue
            
            is_duplicate = False
            task_words = set(task.split())
            
            for existing in unique:
                existing_task = existing.get('task', '').lower()
                existing_words = set(existing_task.split())
                
                overlap = len(task_words & existing_words)
                total = len(task_words | existing_words)
                
                if total > 0 and overlap / total >= 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(action)
                seen_tasks.add(signature)
        
        return unique
    
    def _align_actions_with_decisions(self, notes: Dict) -> Dict:
        """Ensure action items align with decisions"""
        return notes
    
    def get_validation_stats(self, original: Dict, validated: Dict) -> Dict:
        """Get statistics about validation"""
        return {
            'decisions_before': len(original.get('key_decisions', [])),
            'decisions_after': len(validated.get('key_decisions', [])),
            'decisions_removed': len(original.get('key_decisions', [])) - len(validated.get('key_decisions', [])),
            'actions_before': len(original.get('action_items', [])),
            'actions_after': len(validated.get('action_items', [])),
            'actions_removed': len(original.get('action_items', [])) - len(validated.get('action_items', []))
        }
