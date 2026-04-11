"""
PRODUCTION: Advanced Transcript Cleaning
Removes noise, hallucinations, and improves quality
"""
import re
from typing import List, Set, Dict
from langdetect import detect, LangDetectException

class TranscriptCleaner:
    """
    Advanced transcript cleaning with:
    - Filler word removal
    - Hallucination detection
    - Non-English filtering
    - Semantic corrections
    - Normalization
    """
    
    def __init__(self):
        # Filler words to remove
        self.filler_words = {
            'um', 'uh', 'like', 'you know', 'i mean', 'sort of', 
            'kind of', 'basically', 'actually', 'literally',
            'right', 'okay', 'so', 'well', 'yeah', 'yep', 'nope'
        }
        
        # Excessive repetition patterns
        self.repetition_patterns = [
            (r'(\bthank you\b[.,!?]*\s*){3,}', 'Thank you. '),
            (r'(\bobrigado\b[.,!?]*\s*){2,}', ''),
            (r'(\bgracias\b[.,!?]*\s*){2,}', ''),
            (r'(\bmerci\b[.,!?]*\s*){2,}', ''),
            (r'(\bdanke\b[.,!?]*\s*){2,}', ''),
        ]
        
        # Common transcription errors
        self.corrections = {
            'walk outside': 'walk alongside',
            'walkings': 'walk-ins',
            'need their goals': 'meet their goals',
            'need there goals': 'meet their goals',
            'meat their goals': 'meet their goals',
            'slo-kniters': '',
            'slow knitters': '',
        }
        
        # Known hallucination patterns
        self.hallucination_patterns = [
            r'\b[A-Z][a-zá-ž]+\s+[a-zá-ž]+\b',  # Non-English with special chars
            r'\b\w*[ð|þ|æ|ø]\w*\b',  # Nordic characters
            r'\b\w*[ñ|ç|ü|ö|ä]\w*\b',  # Other special chars (if isolated)
        ]
    
    def clean(self, transcript: str, target_language: str = 'en') -> str:
        """
        Comprehensive transcript cleaning
        
        Args:
            transcript: Raw transcript
            target_language: Expected language code (default: 'en')
        
        Returns:
            Cleaned transcript
        """
        if not transcript:
            return transcript
        
        original_length = len(transcript)
        
        # Step 1: Remove excessive filler words
        transcript = self._remove_fillers(transcript)
        
        # Step 2: Remove repetitive patterns
        transcript = self._remove_repetitions(transcript)
        
        # Step 3: Fix common errors
        transcript = self._apply_corrections(transcript)
        
        # Step 4: Remove non-target language content
        transcript = self._filter_language(transcript, target_language)
        
        # Step 5: Remove hallucinations
        transcript = self._remove_hallucinations(transcript)
        
        # Step 6: Normalize whitespace and punctuation
        transcript = self._normalize(transcript)
        
        cleaned_length = len(transcript)
        reduction = ((original_length - cleaned_length) / original_length * 100) if original_length > 0 else 0
        
        if reduction > 10:
            print(f"🧹 Cleaned transcript: {reduction:.1f}% noise removed")
        
        return transcript
    
    def _remove_fillers(self, text: str) -> str:
        """Remove filler words while preserving meaning"""
        for filler in self.filler_words:
            # Remove standalone fillers
            pattern = rf'\b{re.escape(filler)}\b\s*'
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    def _remove_repetitions(self, text: str) -> str:
        """Remove excessive repetitions including noise tail"""
        for pattern, replacement in self.repetition_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Remove trailing noise (repeated thank yous at end)
        text = re.sub(r'(\bthank you\b[.,!?]*\s*)+$', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(\bthanks\b[.,!?]*\s*)+$', '', text, flags=re.IGNORECASE)
        
        # Remove repeated phrases (3+ times)
        words = text.split()
        if len(words) > 10:
            # Detect 3-word phrases repeated 3+ times
            for i in range(len(words) - 8):
                phrase = ' '.join(words[i:i+3])
                count = text.lower().count(phrase.lower())
                if count >= 3:
                    # Keep only first occurrence
                    text = re.sub(rf'({re.escape(phrase)}\s*){{2,}}', phrase + ' ', text, flags=re.IGNORECASE)
        
        return text
    
    def _apply_corrections(self, text: str) -> str:
        """Apply known corrections"""
        for wrong, right in self.corrections.items():
            text = text.replace(wrong, right)
            # Case-insensitive version
            text = re.sub(re.escape(wrong), right, text, flags=re.IGNORECASE)
        
        return text
    
    def _filter_language(self, text: str, target_lang: str) -> str:
        """
        Remove non-target language content
        
        Splits into sentences and removes those in wrong language
        """
        sentences = re.split(r'[.!?]+', text)
        
        filtered_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            if len(sentence) < 10:  # Too short to detect
                filtered_sentences.append(sentence)
                continue
            
            try:
                detected_lang = detect(sentence)
                
                if detected_lang == target_lang or detected_lang == 'en':
                    filtered_sentences.append(sentence)
                else:
                    print(f"🗑️  Removed non-English: '{sentence[:50]}...' (detected: {detected_lang})")
            
            except LangDetectException:
                # Can't detect, keep it
                filtered_sentences.append(sentence)
        
        return '. '.join(filtered_sentences)
    
    def _remove_hallucinations(self, text: str) -> str:
        """
        Remove hallucinated words/phrases
        
        Whisper sometimes hallucinates non-English words
        """
        for pattern in self.hallucination_patterns:
            matches = re.findall(pattern, text)
            
            for match in matches:
                # Check if it's a known English word
                if not self._is_likely_english(match):
                    text = text.replace(match, '')
                    print(f"🗑️  Removed hallucination: '{match}'")
        
        return text
    
    def _is_likely_english(self, word: str) -> bool:
        """Check if word is likely English"""
        # Simple heuristic: English words don't have special characters
        special_chars = set('áéíóúàèìòùâêîôûäëïöüñçþðæø')
        
        return not any(c.lower() in special_chars for c in word)
    
    def _normalize(self, text: str) -> str:
        """Normalize whitespace and punctuation"""
        # Remove multiple spaces
        text = ' '.join(text.split())
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,!?])', r'\1', text)
        text = re.sub(r'([.,!?])([A-Z])', r'\1 \2', text)
        
        # Remove multiple punctuation
        text = re.sub(r'([.!?])\1+', r'\1', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def assess_quality(self, transcript: str) -> Dict:
        """
        Assess transcript quality
        
        Returns:
            {
                'score': 0.0-1.0,
                'issues': [...],
                'recommendations': [...]
            }
        """
        issues = []
        recommendations = []
        score = 1.0
        
        words = transcript.split()
        word_count = len(words)
        
        # Check length
        if word_count < 20:
            issues.append("Very short transcript")
            recommendations.append("Ensure audio is clear and complete")
            score -= 0.3
        
        # Check repetition
        unique_words = len(set(word.lower() for word in words))
        repetition_ratio = unique_words / word_count if word_count > 0 else 0
        
        if repetition_ratio < 0.3:
            issues.append("High repetition (low uniqueness)")
            recommendations.append("Check for audio quality issues")
            score -= 0.2
        
        # Check for filler words
        filler_count = sum(1 for word in words if word.lower() in self.filler_words)
        filler_ratio = filler_count / word_count if word_count > 0 else 0
        
        if filler_ratio > 0.1:
            issues.append(f"High filler word ratio ({filler_ratio:.1%})")
            recommendations.append("Consider using cleaner audio")
            score -= 0.1
        
        # Check for non-English content
        try:
            detected_lang = detect(transcript)
            if detected_lang != 'en':
                issues.append(f"Non-English content detected ({detected_lang})")
                recommendations.append("Ensure audio is in English")
                score -= 0.2
        except:
            pass
        
        return {
            'score': max(score, 0.0),
            'issues': issues,
            'recommendations': recommendations,
            'word_count': word_count,
            'uniqueness': repetition_ratio
        }


# Example usage
if __name__ == "__main__":
    cleaner = TranscriptCleaner()
    
    # Test with noisy transcript
    noisy_transcript = """
    Um, so, like, thank you. Thank you. Thank you. Obrigado. Obrigado.
    We need to, uh, walk outside people to, like, need their goals.
    Eitthvað gráður slo-kniters and stuff.
    The Cambridge Community House Trust provides support services.
    """
    
    print("Original:")
    print(noisy_transcript)
    print("\n" + "="*70 + "\n")
    
    # Clean
    cleaned = cleaner.clean(noisy_transcript)
    
    print("Cleaned:")
    print(cleaned)
    print("\n" + "="*70 + "\n")
    
    # Assess quality
    quality = cleaner.assess_quality(cleaned)
    
    print(f"Quality Score: {quality['score']:.2f}")
    print(f"Word Count: {quality['word_count']}")
    print(f"Uniqueness: {quality['uniqueness']:.2f}")
    
    if quality['issues']:
        print("\nIssues:")
        for issue in quality['issues']:
            print(f"  - {issue}")
    
    if quality['recommendations']:
        print("\nRecommendations:")
        for rec in quality['recommendations']:
            print(f"  - {rec}")
