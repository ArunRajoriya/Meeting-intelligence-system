"""
Formal Meeting Entity Extractor
Specialized extraction for council/government meetings
"""
import re
from typing import Dict, List

class FormalMeetingExtractor:
    """
    Extract entities specific to formal meetings
    
    Extracts:
    - Locations (roads, areas, facilities)
    - Public concerns (safety, traffic, noise)
    - Policy areas (bylaws, regulations)
    - Officials (councillors, staff)
    """
    
    def __init__(self):
        # Location patterns
        self.location_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:road|street|avenue|drive|lane|boulevard|way)\b',
            r'\b(?:on|at|near|along)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'\b([A-Z][a-z]+\s+Point)\b',  # Grand Point, etc.
        ]
        
        # Public concern keywords
        self.concern_keywords = {
            'safety': ['safety', 'dangerous', 'hazard', 'risk', 'concern', 'worried'],
            'traffic': ['speeding', 'traffic', 'speed', 'vehicles', 'cars', 'driving'],
            'noise': ['noise', 'loud', 'disturbance', 'complaint'],
            'crime': ['crime', 'theft', 'vandalism', 'mischief', 'break-in'],
            'infrastructure': ['road', 'sidewalk', 'lighting', 'maintenance', 'repair']
        }
        
        # Official titles
        self.official_titles = [
            'councillor', 'mayor', 'staff sergeant', 'sergeant', 'chief',
            'ceo', 'assistant ceo', 'director', 'manager', 'officer'
        ]
    
    def extract_formal_entities(self, transcript: str) -> Dict:
        """
        Extract entities from formal meeting transcript
        
        Returns:
            {
                'locations': [...],
                'public_concerns': {...},
                'officials': [...],
                'policy_areas': [...]
            }
        """
        # Extract locations
        locations = self._extract_locations(transcript)
        
        # Extract public concerns
        concerns = self._extract_concerns(transcript)
        
        # Extract officials
        officials = self._extract_officials(transcript)
        
        # Extract policy areas
        policy_areas = self._extract_policy_areas(transcript)
        
        return {
            'locations': locations,
            'public_concerns': concerns,
            'officials': officials,
            'policy_areas': policy_areas
        }
    
    def _extract_locations(self, transcript: str) -> List[Dict]:
        """Extract location mentions"""
        locations = []
        seen = set()
        
        for pattern in self.location_patterns:
            matches = re.finditer(pattern, transcript, re.IGNORECASE)
            
            for match in matches:
                location = match.group(1).strip()
                
                # Clean up
                location = self._clean_location_name(location)
                
                if location and location.lower() not in seen:
                    # Find context (what's being discussed about this location)
                    context = self._find_location_context(location, transcript)
                    
                    locations.append({
                        'name': location,
                        'context': context
                    })
                    
                    seen.add(location.lower())
        
        return locations
    
    def _clean_location_name(self, location: str) -> str:
        """Clean up location name"""
        # Remove common prefixes
        location = re.sub(r'^(?:the|a|an)\s+', '', location, flags=re.IGNORECASE)
        
        # Capitalize properly
        words = location.split()
        location = ' '.join(word.capitalize() for word in words)
        
        return location
    
    def _find_location_context(self, location: str, transcript: str) -> str:
        """Find what's being discussed about this location"""
        # Find sentences mentioning this location
        sentences = re.split(r'[.!?]+', transcript)
        
        for sentence in sentences:
            if location.lower() in sentence.lower():
                # Extract key concerns from this sentence
                concerns = []
                
                for concern_type, keywords in self.concern_keywords.items():
                    if any(keyword in sentence.lower() for keyword in keywords):
                        concerns.append(concern_type)
                
                if concerns:
                    return ', '.join(concerns)
        
        return 'general discussion'
    
    def _extract_concerns(self, transcript: str) -> Dict:
        """Extract public concerns by category"""
        concerns = {}
        
        for concern_type, keywords in self.concern_keywords.items():
            mentions = []
            
            # Find sentences with these keywords
            sentences = re.split(r'[.!?]+', transcript)
            
            for sentence in sentences:
                sentence = sentence.strip()
                
                if any(keyword in sentence.lower() for keyword in keywords):
                    # Extract the specific concern
                    concern = self._extract_specific_concern(sentence, keywords)
                    
                    if concern and concern not in mentions:
                        mentions.append(concern)
            
            if mentions:
                concerns[concern_type] = mentions
        
        return concerns
    
    def _extract_specific_concern(self, sentence: str, keywords: List[str]) -> str:
        """Extract specific concern from sentence"""
        # Clean up sentence
        sentence = sentence.strip()
        
        # Limit length
        if len(sentence) > 150:
            sentence = sentence[:150] + "..."
        
        return sentence
    
    def _extract_officials(self, transcript: str) -> List[Dict]:
        """Extract official names and titles"""
        officials = []
        seen = set()
        
        # Pattern: Title Name
        for title in self.official_titles:
            pattern = rf'\b{re.escape(title)}\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
            
            matches = re.finditer(pattern, transcript, re.IGNORECASE)
            
            for match in matches:
                name = match.group(1).strip()
                
                if name and name.lower() not in seen:
                    officials.append({
                        'name': name,
                        'title': title.title()
                    })
                    
                    seen.add(name.lower())
        
        return officials
    
    def _extract_policy_areas(self, transcript: str) -> List[str]:
        """Extract policy areas being discussed"""
        policy_keywords = [
            'bylaw', 'regulation', 'policy', 'ordinance', 'statute',
            'traffic', 'zoning', 'development', 'safety', 'budget'
        ]
        
        areas = []
        
        for keyword in policy_keywords:
            if keyword in transcript.lower():
                areas.append(keyword.title())
        
        return list(set(areas))
    
    def format_for_summary(self, entities: Dict) -> str:
        """Format entities for inclusion in summary"""
        lines = []
        
        if entities['locations']:
            lines.append("LOCATIONS DISCUSSED:")
            for loc in entities['locations']:
                lines.append(f"  • {loc['name']}: {loc['context']}")
        
        if entities['public_concerns']:
            lines.append("\nPUBLIC CONCERNS:")
            for concern_type, mentions in entities['public_concerns'].items():
                lines.append(f"  • {concern_type.title()}: {len(mentions)} mention(s)")
        
        if entities['officials']:
            lines.append("\nOFFICIALS PRESENT:")
            for official in entities['officials']:
                lines.append(f"  • {official['title']} {official['name']}")
        
        return '\n'.join(lines)


# Example usage
if __name__ == "__main__":
    extractor = FormalMeetingExtractor()
    
    # Test with council meeting transcript
    transcript = """
    Staff Sergeant Ron Poydor presented statistics on traffic offenses.
    Councillor Jason Bodner asked about safety concerns on Bernat road.
    A resident complained about speeding on the old 59 through Grand Point.
    The council discussed increasing police presence in the area.
    Councillor Belanger mentioned concerns about crime in the community.
    """
    
    print("="*70)
    print("FORMAL MEETING ENTITY EXTRACTION TEST")
    print("="*70)
    
    entities = extractor.extract_formal_entities(transcript)
    
    print("\n📍 LOCATIONS:")
    for loc in entities['locations']:
        print(f"  • {loc['name']}: {loc['context']}")
    
    print("\n⚠️  PUBLIC CONCERNS:")
    for concern_type, mentions in entities['public_concerns'].items():
        print(f"  • {concern_type.title()}: {len(mentions)} mention(s)")
        for mention in mentions[:2]:  # Show first 2
            print(f"    - {mention[:80]}...")
    
    print("\n👥 OFFICIALS:")
    for official in entities['officials']:
        print(f"  • {official['title']} {official['name']}")
    
    print("\n📋 POLICY AREAS:")
    for area in entities['policy_areas']:
        print(f"  • {area}")
    
    print("\n" + "="*70)
    print("FORMATTED SUMMARY")
    print("="*70)
    print(extractor.format_for_summary(entities))
