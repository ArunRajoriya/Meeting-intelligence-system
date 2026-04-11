"""
PRODUCTION: Named Entity Recognition
Extracts: People, Organizations, Money, Dates, Locations
"""
import re
from typing import Dict, List
from collections import defaultdict

class EntityExtractor:
    """
    Extract named entities from meeting transcripts
    
    Entities:
    - PERSON: Names of people
    - ORGANIZATION: Companies, NGOs, institutions
    - MONEY: Dollar amounts, budgets
    - DATE: Dates, deadlines, timeframes
    - LOCATION: Places, addresses
    - NUMBER: Quantities, statistics
    """
    
    def __init__(self):
        # Try to use spaCy if available
        self.nlp = None
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            print("✅ Using spaCy for NER")
        except:
            print("⚠️  spaCy not available, using regex-based NER")
            print("💡 Install: python -m spacy download en_core_web_sm")
    
    def extract(self, text: str) -> Dict[str, List[str]]:
        """
        Extract all entities from text
        
        Returns:
            {
                'PERSON': ['John Smith', 'Sarah Johnson'],
                'ORG': ['Cambridge Community House Trust'],
                'MONEY': ['$50,000', '$75K'],
                'DATE': ['Friday', 'next week', 'May 8th'],
                'GPE': ['Cambridge', 'New Zealand'],
                'CARDINAL': ['42', '100']
            }
        """
        if self.nlp:
            return self._extract_with_spacy(text)
        else:
            return self._extract_with_regex(text)
    
    def _extract_with_spacy(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using spaCy"""
        doc = self.nlp(text)
        
        entities = defaultdict(list)
        
        for ent in doc.ents:
            entities[ent.label_].append(ent.text)
        
        # Deduplicate
        for label in entities:
            entities[label] = list(set(entities[label]))
        
        return dict(entities)
    
    def _extract_with_regex(self, text: str) -> Dict[str, List[str]]:
        """Fallback: Extract entities using regex patterns"""
        entities = defaultdict(list)
        
        # MONEY patterns
        money_patterns = [
            r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?(?:\s*(?:thousand|million|billion|K|M|B))?',
            r'\d+(?:,\d{3})*\s*dollars?',
        ]
        
        for pattern in money_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['MONEY'].extend(matches)
        
        # DATE patterns
        date_patterns = [
            r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?\b',
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\b(?:next|last|this)\s+(?:week|month|year|Monday|Tuesday|Wednesday|Thursday|Friday)\b',
            r'\b(?:tomorrow|today|yesterday)\b',
            r'\bby\s+(?:Friday|Monday|Tuesday|Wednesday|Thursday|next week|end of month)\b',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['DATE'].extend(matches)
        
        # PERSON patterns (capitalized names)
        person_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b'
        matches = re.findall(person_pattern, text)
        
        # Filter out common words
        common_words = {'The', 'This', 'That', 'These', 'Those', 'There', 'Where', 'When'}
        persons = [m for m in matches if m not in common_words]
        entities['PERSON'].extend(persons)
        
        # ORGANIZATION patterns
        org_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Trust|Foundation|Organization|Association|Committee|Council|Board|Company|Corporation|Inc|Ltd))\b',
            r'\b([A-Z][A-Z]+)\b',  # Acronyms
        ]
        
        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            entities['ORG'].extend(matches)
        
        # NUMBER patterns
        number_pattern = r'\b\d+(?:,\d{3})*(?:\.\d+)?\b'
        matches = re.findall(number_pattern, text)
        entities['CARDINAL'].extend(matches)
        
        # LOCATION patterns (cities, countries)
        # This is basic - spaCy does much better
        location_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b(?=\s+(?:City|Town|Village|County|State|Country))'
        matches = re.findall(location_pattern, text)
        entities['GPE'].extend(matches)
        
        # Deduplicate
        for label in entities:
            entities[label] = list(set(entities[label]))
        
        return dict(entities)
    
    def extract_key_entities(self, text: str) -> Dict:
        """
        Extract and categorize key entities for meeting intelligence
        
        Returns:
            {
                'people': [...],
                'organizations': [...],
                'money_amounts': [...],
                'dates': [...],
                'locations': [...],
                'numbers': [...]
            }
        """
        raw_entities = self.extract(text)
        
        return {
            'people': raw_entities.get('PERSON', []),
            'organizations': raw_entities.get('ORG', []),
            'money_amounts': raw_entities.get('MONEY', []),
            'dates': raw_entities.get('DATE', []),
            'locations': raw_entities.get('GPE', []),
            'numbers': raw_entities.get('CARDINAL', [])
        }
    
    def extract_funding_info(self, text: str) -> Dict:
        """
        Extract funding-specific information
        
        Returns:
            {
                'requested_amount': '$50,000',
                'current_funding': '$25,000',
                'funding_gap': '$25,000',
                'funding_purpose': 'community services'
            }
        """
        funding_info = {}
        
        # Extract requested amounts
        request_patterns = [
            r'request(?:ing)?\s+(?:for\s+)?(\$\s*\d+(?:,\d{3})*(?:\s*K)?)',
            r'need(?:ing)?\s+(\$\s*\d+(?:,\d{3})*(?:\s*K)?)',
            r'seeking\s+(\$\s*\d+(?:,\d{3})*(?:\s*K)?)',
        ]
        
        for pattern in request_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                funding_info['requested_amount'] = match.group(1)
                break
        
        # Extract funding gaps
        gap_patterns = [
            r'(?:funding\s+)?gap\s+of\s+(\$\s*\d+(?:,\d{3})*)',
            r'shortfall\s+of\s+(\$\s*\d+(?:,\d{3})*)',
            r'deficit\s+of\s+(\$\s*\d+(?:,\d{3})*)',
        ]
        
        for pattern in gap_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                funding_info['funding_gap'] = match.group(1)
                break
        
        # Extract purpose
        purpose_patterns = [
            r'funding\s+for\s+([^.,]+)',
            r'support\s+(?:for\s+)?([^.,]+)',
            r'budget\s+for\s+([^.,]+)',
        ]
        
        for pattern in purpose_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                funding_info['funding_purpose'] = match.group(1).strip()
                break
        
        return funding_info
    
    def extract_statistics(self, text: str) -> List[Dict]:
        """
        Extract statistics and metrics
        
        Returns:
            [
                {'value': '42', 'context': 'families supported'},
                {'value': '100%', 'context': 'increase in demand'}
            ]
        """
        statistics = []
        
        # Pattern: number + context
        patterns = [
            r'(\d+(?:,\d{3})*)\s+([a-z\s]+(?:supported|served|helped|assisted))',
            r'(\d+%)\s+([a-z\s]+)',
            r'increase\s+of\s+(\d+%?)',
            r'decrease\s+of\s+(\d+%?)',
            r'(\d+)\s+(?:times|fold)\s+(?:increase|more)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                statistics.append({
                    'value': match.group(1),
                    'context': match.group(2) if match.lastindex >= 2 else match.group(0)
                })
        
        return statistics


# Example usage
if __name__ == "__main__":
    extractor = EntityExtractor()
    
    # Test with sample text
    sample_text = """
    Harriet Dixon from Cambridge Community House Trust presented a funding request.
    The organization supports 42 families weekly and needs $50,000 for community services.
    The funding gap has increased due to COVID-19 impact.
    Mike Chen and Sarah Johnson are board members.
    The meeting is scheduled for next Friday at 10 AM.
    """
    
    print("Sample Text:")
    print(sample_text)
    print("\n" + "="*70 + "\n")
    
    # Extract all entities
    entities = extractor.extract_key_entities(sample_text)
    
    print("Extracted Entities:")
    for entity_type, values in entities.items():
        if values:
            print(f"\n{entity_type.upper()}:")
            for value in values:
                print(f"  - {value}")
    
    # Extract funding info
    print("\n" + "="*70 + "\n")
    funding = extractor.extract_funding_info(sample_text)
    
    if funding:
        print("Funding Information:")
        for key, value in funding.items():
            print(f"  {key}: {value}")
    
    # Extract statistics
    print("\n" + "="*70 + "\n")
    stats = extractor.extract_statistics(sample_text)
    
    if stats:
        print("Statistics:")
        for stat in stats:
            print(f"  {stat['value']} - {stat['context']}")
