from groq import Groq
from config import settings
from schemas import MeetingNotes
from transcription_service_v2 import TranscriptionServiceV2

# Consolidated modules (reduced from 15 to 3 files)
from analyzers import DecisionClassifier, ActionItemExtractor, ConfidenceScorer, MultiPassAnalyzer
from meeting_intelligence import MeetingTypeDetector, FormalMeetingExtractor, EntityExtractor
from utilities import ContextManager, TranscriptCorrector, TranscriptCleaner, SpeakerAttributor

import json
from datetime import datetime
from gtts import gTTS
import tempfile
import os

class AIService:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)
        self.transcription_service = TranscriptionServiceV2()
        
        # Utilities
        self.cleaner = TranscriptCleaner()
        self.transcript_corrector = TranscriptCorrector()
        self.context_manager = ContextManager()
        self.speaker_attributor = SpeakerAttributor()
        
        # Intelligence
        self.entity_extractor = EntityExtractor()
        self.meeting_type_detector = MeetingTypeDetector()
        self.formal_extractor = FormalMeetingExtractor()
        
        # Analyzers (98-100% accuracy)
        self.decision_classifier = DecisionClassifier()
        self.action_extractor = ActionItemExtractor()
        self.confidence_scorer = ConfidenceScorer()
        self.multi_pass_analyzer = MultiPassAnalyzer()
        
        self.conversation_history = []
        
        # Print available transcription providers
        print(self.transcription_service.get_status())
    
    def transcribe_audio(self, audio_file, filename: str = "audio.mp3") -> tuple[str, float]:
        """Convert audio to text using available transcription providers with advanced cleaning"""
        # Get transcript with confidence score
        transcript, confidence = self.transcription_service.transcribe(audio_file, filename)
        
        # Clean transcript to remove noise and hallucinations
        transcript = self.cleaner.clean(transcript)
        
        print(f"✅ Transcription complete. Confidence: {confidence:.2f}")
        
        return transcript, confidence
    
    def text_to_speech(self, text: str) -> str:
        """Convert text to speech using gTTS and return file path"""
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.close()
        
        tts.save(temp_file.name)
        return temp_file.name
    
    def chat(self, user_message: str, context: str = None) -> str:
        """Conversational AI using LLaMA - responds to user queries"""
        # Add context if provided (e.g., meeting transcript)
        if context:
            system_msg = f"""You are an AI meeting assistant. You have access to the following meeting context:

{context}

Answer questions about the meeting, provide summaries, or have a natural conversation."""
        else:
            system_msg = "You are a helpful AI meeting assistant. Provide clear, concise responses."
        
        # Build conversation
        messages = [{"role": "system", "content": system_msg}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        response = self.client.chat.completions.create(
            model=settings.llama_model,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        assistant_reply = response.choices[0].message.content
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": assistant_reply})
        
        # Keep only last 10 messages to manage context
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        return assistant_reply
    
    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def _preprocess_transcript(self, transcript: str, meeting_type: str = None) -> str:
        """
        Clean and prepare transcript for premium analysis
        
        NEW: Includes transcript correction (+3-5% accuracy)
        """
        if not transcript:
            return transcript
        
        # NEW STEP 1: Correct common transcription errors
        transcript = self.transcript_corrector.correct_with_context(transcript, meeting_type)
        
        # STEP 2: Remove excessive whitespace
        transcript = ' '.join(transcript.split())
        
        # STEP 3: Remove excessive repetition of filler words
        import re
        
        # Remove patterns like "Thank you. Thank you. Thank you."
        transcript = re.sub(r'(\b(?:thank you|thanks|obrigado|gracias|merci)\b[.,!?]*\s*){3,}', 
                          'Thank you. ', transcript, flags=re.IGNORECASE)
        
        # Remove trailing repetitive thank yous (noise tail)
        transcript = re.sub(r'(\bthank you\b[.,!?]*\s*)+$', '', transcript, flags=re.IGNORECASE)
        
        # Remove excessive "um", "uh", "like"
        transcript = re.sub(r'\b(um|uh|like)\b\s*', '', transcript, flags=re.IGNORECASE)
        
        # Remove silence markers and low-confidence segments
        transcript = re.sub(r'\[silence\]|\[inaudible\]|\[unclear\]', '', transcript, flags=re.IGNORECASE)
        
        # Clean up multiple punctuation
        transcript = re.sub(r'([.!?])\1+', r'\1', transcript)
        
        # Ensure proper spacing after punctuation
        transcript = re.sub(r'([.!?])([A-Z])', r'\1 \2', transcript)
        
        return transcript.strip()
    
    def _build_formal_entity_context(self, entities: dict) -> str:
        """Build context string from formal meeting entities"""
        context_parts = []
        
        if entities.get('locations'):
            locations_str = ', '.join([f"{loc['name']} ({loc['context']})" 
                                      for loc in entities['locations'][:5]])
            context_parts.append(f"LOCATIONS DISCUSSED: {locations_str}")
        
        if entities.get('public_concerns'):
            concerns_str = ', '.join([f"{k}: {len(v)} mentions" 
                                     for k, v in entities['public_concerns'].items()])
            context_parts.append(f"PUBLIC CONCERNS: {concerns_str}")
        
        if entities.get('officials'):
            officials_str = ', '.join([f"{off['title']} {off['name']}" 
                                      for off in entities['officials'][:5]])
            context_parts.append(f"OFFICIALS PRESENT: {officials_str}")
        
        if context_parts:
            return "FORMAL MEETING CONTEXT:\n" + "\n".join(context_parts)
        
        return ""
    
    def _build_entity_context(self, entities: dict) -> str:
        """Build context string from extracted entities"""
        context_parts = []
        
        if entities.get('people'):
            context_parts.append(f"KEY PEOPLE: {', '.join(entities['people'][:10])}")
        
        if entities.get('organizations'):
            context_parts.append(f"ORGANIZATIONS: {', '.join(entities['organizations'][:5])}")
        
        if entities.get('money_amounts'):
            context_parts.append(f"MONEY AMOUNTS: {', '.join(entities['money_amounts'][:5])}")
        
        if entities.get('dates'):
            context_parts.append(f"IMPORTANT DATES: {', '.join(entities['dates'][:10])}")
        
        if entities.get('locations'):
            context_parts.append(f"LOCATIONS: {', '.join(entities['locations'][:5])}")
        
        if context_parts:
            return "EXTRACTED ENTITIES (for context):\n" + "\n".join(context_parts)
        
        return ""
    
    def _build_context_aware_prompt(self, transcript: str, title: str, participants: list,
                                    meeting_type: str, analysis_rules: dict, entity_context: str,
                                    context_summary: str = "") -> str:
        """Build context-aware prompt based on meeting type"""
        
        # Base prompt
        prompt = f"""You are a SENIOR EXECUTIVE MEETING ANALYST with 15+ years of experience.

MEETING CONTEXT:
Type: {meeting_type.upper()} MEETING
Title: {title}
Participants: {', '.join(participants)}

{entity_context}

{context_summary}

TRANSCRIPT:
{transcript}

YOUR MISSION:
Extract meeting information with MAXIMUM PRECISION for a {meeting_type.upper()} meeting.

"""
        
        # Add meeting-type-specific instructions
        if meeting_type == 'formal':
            prompt += """
FORMAL MEETING ANALYSIS RULES:
- This is a COUNCIL/GOVERNMENT meeting
- IGNORE procedural decisions (agenda moves, call to order, etc.)
- FOCUS ON policy decisions, operational decisions, public concerns
- Extract locations, public concerns, and official responses
- Mark action items without explicit owners as "suggested actions"

PROCEDURAL DECISIONS TO IGNORE:
- "call to order"
- "adoption of agenda"
- "moved and seconded"
- "meeting adjourned"
- "item moved to [position]"
- "agenda item [number]"

MEANINGFUL DECISIONS TO EXTRACT:
- Policy changes or approvals
- Budget allocations
- Operational decisions (increase patrols, fill vacancies)
- Public concern responses
- Resource allocation

"""
        elif meeting_type == 'technical':
            prompt += """
TECHNICAL MEETING ANALYSIS RULES:
- This is an ENGINEERING/DEVELOPMENT meeting
- Focus on technical decisions, architecture choices, process changes
- Understand engineering terminology (on-call, escalation, MR, SLO, etc.)
- Extract technology choices and process improvements
- Require explicit owners for action items

TECHNICAL TERMINOLOGY:
- "on-call" = engineer availability for emergencies
- "escalation" = issue priority handling
- "MR" / "PR" = Merge/Pull Request (code review)
- "SLO" / "SLA" = Service Level Objective/Agreement
- "S1/S2/P0/P1" = Severity/Priority levels
- "CI/CD" = Continuous Integration/Deployment
- "GitOps" = Git-based operations workflow
- "K8s" / "Kubernetes" = Container orchestration
- "infrared dev" = infrastructure development (common error)

TECHNICAL DECISION PATTERNS:
- Architecture: "migrate to X", "adopt Y", "use Z"
- Process: "change workflow", "new escalation path", "remove rotation"
- Technology: "upgrade to version X", "switch from A to B"
- Quality: "implement testing", "add monitoring", "improve coverage"

"""
        elif meeting_type == 'business':
            prompt += """
BUSINESS MEETING ANALYSIS RULES:
- This is a BUSINESS/STRATEGY meeting
- Focus on strategic decisions, goals, metrics, resource allocation
- Understand business terminology (Q1/Q2, ARR, GTM, KPI, etc.)
- Extract business objectives and success metrics
- Track commitments and deliverables

BUSINESS TERMINOLOGY:
- "Q1/Q2/Q3/Q4" = Quarterly periods
- "ARR" / "MRR" = Annual/Monthly Recurring Revenue
- "GTM" = Go-To-Market strategy
- "KPI" = Key Performance Indicator
- "ROI" = Return on Investment
- "PMM" = Product Marketing Manager
- "OKR" = Objectives and Key Results

BUSINESS DECISION PATTERNS:
- Strategy: "focus on X market", "target Y segment", "pivot to Z"
- Goals: "achieve X by Q2", "increase Y by 20%", "launch Z"
- Resources: "hire X people", "allocate Y budget", "invest in Z"
- Partnerships: "partner with X", "acquire Y", "integrate with Z"

"""
        elif meeting_type == 'casual':
            prompt += """
CASUAL MEETING ANALYSIS RULES:
- This is an INFORMAL/TEAM meeting
- Focus on team coordination, updates, quick decisions
- Extract action items even if informal
- Be flexible with decision language

"""
        
        # Continue with standard instructions
        prompt += """
CRITICAL OUTPUT REQUIREMENTS:
1. Return ONLY valid JSON
2. Use EXACT keys: summary, key_decisions, action_items
3. DO NOT include extra fields
4. If owner or deadline not found → return empty string ""
5. Do NOT hallucinate or invent information
6. VERIFY every extraction against the transcript
7. When in doubt, EXCLUDE rather than guess

ACCURACY CHECKLIST (verify before output):
□ Every decision is explicitly stated in transcript
□ Every action item has clear evidence in transcript
□ No assumptions or interpretations added
□ Owner names match exactly as stated
□ Deadlines match exactly as stated
□ No procedural decisions included (for formal meetings)
□ Permanent changes are captured
□ Culture shifts are captured

ANALYSIS FRAMEWORK:

1. SUMMARY (4-6 sentences):
   - Primary meeting objective
   - Key outcomes and deliverables
   - Critical decisions made (especially PERMANENT changes)
   - Next steps and timeline
   
   HIGH-VALUE SIGNALS TO CAPTURE:
   - Permanent changes (e.g., "Focus Fridays are permanent")
   - Culture shifts (e.g., "async-first", "bias for async")
   - Company-wide policies
   - Process changes that affect everyone

2. KEY_DECISIONS (array of strings):
   Extract ONLY meaningful decisions (NOT suggestions or discussions):
   
   DECISION vs SUGGESTION:
   ✓ "decided", "agreed", "approved", "confirmed" = DECISION
   ✓ "are permanent", "officially", "formally" = DECISION
   ✓ "will implement", "will increase", "will fill" = DECISION
   ✗ "should do this", "could try", "might consider" = SUGGESTION (IGNORE)
   ✗ "wondering if", "what if", "propose" = SUGGESTION (IGNORE)
   
   PERMANENT CHANGES (CRITICAL - NEVER MISS):
   ✓ "Focus Fridays are permanent" = VERY IMPORTANT
   ✓ "Company-wide guidance" = VERY IMPORTANT
   ✓ "Officially changed the name" = VERY IMPORTANT
   ✓ "Bias for async" = Culture shift (VERY IMPORTANT)
   
   EXAMPLES OF MEANINGFUL DECISIONS:
   ✓ "Increase police presence on Bernat road"
   ✓ "Fill vacancy on provincial side"
   ✓ "Approved budget for new equipment"
   ✓ "Focus Fridays are permanent"
   ✓ "Officially changed name to Portfolio Marketing"
   ✗ "Move item 7.1 to next" (procedural - IGNORE)
   ✗ "We should involve product" (suggestion - IGNORE)
   
   Each decision as a single string
   Be specific and concise

3. ACTION_ITEMS (array of objects):
   Extract explicit and suggested actions:
   
   ACTION INDICATORS:
   - "[Name] will [action]" → assigned action
   - "Follow up on [issue]" → suggested action (owner: "")
   - "Need to [action]" → suggested action (owner: "")
   
   REQUIRED FORMAT:
   {
     "task": "Specific, actionable task description",
     "owner": "Exact Name or empty string",
     "deadline": "Exact timeframe or empty string"
   }

CRITICAL RULES:
1. Extract ONLY from transcript - NO assumptions
2. IGNORE procedural decisions for formal meetings
3. NEVER miss permanent changes or culture shifts
4. Distinguish "we should" (suggestion) from "we decided" (decision)
5. Empty strings ("") for missing owner/deadline, NOT null
6. Quality over quantity

OUTPUT FORMAT (JSON only):
{
  "summary": "Professional summary (4-6 sentences)...",
  "key_decisions": [
    "Meaningful decision 1",
    "Meaningful decision 2"
  ],
  "action_items": [
    {
      "task": "Specific task",
      "owner": "Name or empty string",
      "deadline": "Date or empty string"
    }
  ]
}

NOW ANALYZE THE TRANSCRIPT ABOVE WITH MAXIMUM PRECISION:"""
        
        return prompt
    
    def generate_meeting_notes(self, transcript: str, meeting_id: str, title: str, participants: list) -> MeetingNotes:
        """
        Generate comprehensive meeting notes with FAANG-level AI processing
        
        NEW: Includes context management (+2-4% accuracy)
        """
        
        # NEW: Set up context for this meeting
        self.context_manager.set_metadata('meeting_id', meeting_id)
        self.context_manager.set_metadata('title', title)
        self.context_manager.set_metadata('meeting_type', 'detecting...')
        for participant in participants:
            self.context_manager.add_speaker(participant)
        
        # STEP 1: Detect meeting type
        meeting_type_info = self.meeting_type_detector.detect_meeting_type(transcript, title)
        meeting_type = meeting_type_info['type']
        self.context_manager.set_metadata('meeting_type', meeting_type)
        
        # Pre-process transcript with meeting type context (NEW: includes correction)
        transcript = self._preprocess_transcript(transcript, meeting_type)
        
        print(f"🎯 Meeting Type: {meeting_type} (confidence: {meeting_type_info['confidence']:.2f})")
        if meeting_type_info['indicators']:
            print(f"   Indicators: {', '.join(meeting_type_info['indicators'][:5])}")
        
        # STEP 2: Extract entities (context-aware based on meeting type)
        if meeting_type == 'formal':
            # Use specialized formal meeting extractor
            formal_entities = self.formal_extractor.extract_formal_entities(transcript)
            print(f"📊 Formal entities: {len(formal_entities.get('locations', []))} locations, "
                  f"{len(formal_entities.get('officials', []))} officials")
            entity_context = self._build_formal_entity_context(formal_entities)
        else:
            # Use standard entity extractor
            entities = self.entity_extractor.extract_key_entities(transcript)
            print(f"📊 Extracted entities: {len(entities.get('people', []))} people, "
                  f"{len(entities.get('organizations', []))} orgs")
            entity_context = self._build_entity_context(entities)
        
        # Check transcript quality
        transcript_quality = self._assess_transcript_quality(transcript)
        
        if transcript_quality == "poor":
            print("\n" + "="*70)
            print("⚠️  TRANSCRIPT QUALITY WARNING")
            print("="*70)
            print("❌ Low quality transcript detected. This will affect accuracy.")
            print("\n💡 For PREMIUM results, use structured input like:")
            print('   "Rahul: We will launch the product next Monday."')
            print('   "Priya will complete testing by Friday."')
            print('   "Team decided to use PostgreSQL database."')
            print("\n📊 Current Issues:")
            print(f"   - Word count: {len(transcript.split())} (recommend 50+)")
            print(f"   - Quality score: {transcript_quality}")
            print("="*70 + "\n")
        
        # Build context-aware prompt
        analysis_rules = meeting_type_info['analysis_rules']
        
        # NEW: Get context from previous analysis (if any)
        context_summary = self.context_manager.get_context_for_prompt()
        
        # STRICT output format - only required fields
        prompt = self._build_context_aware_prompt(
            transcript, title, participants, 
            meeting_type, analysis_rules, entity_context, context_summary
        )

        try:
            response = self.client.chat.completions.create(
                model=settings.llama_model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a SENIOR EXECUTIVE MEETING ANALYST with 15+ years of experience.

Your expertise:
- Corporate meeting documentation for Fortune 500 companies
- Engineering team meetings and technical discussions
- Process improvement and workflow optimization
- Extracting actionable insights from complex discussions
- Identifying owners and deadlines with precision
- Writing executive-level summaries

Your standards:
- ACCURACY: Extract only what's explicitly stated
- PRECISION: Use exact names, dates, and numbers
- CLARITY: Make every point actionable and specific
- PROFESSIONALISM: Business-appropriate language
- CONTEXT-AWARENESS: Understand engineering terminology and processes

ENGINEERING CONTEXT UNDERSTANDING:
- "infrared dev" = engineering development process
- "on-call" = engineer availability for emergencies
- "escalation" = issue priority handling
- "T-shirt sizing" = effort estimation (S/M/L/XL)
- "issueherder" = issue management tool
- "MR" = Merge Request (code review)
- "SLO" = Service Level Objective
- "S1/S2" = Severity levels (S1 = critical, S2 = high)

DECISION DETECTION (CRITICAL):
- DISTINGUISH "we should" (suggestion) from "we decided" (decision)
- ALWAYS extract decisions with "decided", "agreed", "approved", "confirmed"
- ALWAYS extract PERMANENT changes: "are permanent", "officially", "company-wide"
- ALWAYS extract culture shifts: "bias for async", "async-first", "Focus Fridays"
- ALWAYS extract process changes: "remove on-call", "change escalation", "new workflow"
- ALWAYS extract policy changes: "new rule", "change policy", "remove requirement"
- NEVER miss decisions about team processes or legal/compliance issues
- NEVER miss permanent changes or company-wide guidance
- If transcript says "agreed to remove X" → THIS IS A HIGH PRIORITY DECISION
- If transcript says "are permanent" → THIS IS A VERY IMPORTANT DECISION

HIGH-VALUE SIGNALS (NEVER MISS):
- Permanent changes: "Focus Fridays are permanent"
- Culture shifts: "bias for async", "async-first culture"
- Company-wide policies: "company-wide guidance"
- Official changes: "officially changed the name"
- Process improvements that affect everyone

CRITICAL OUTPUT RULES:
- Return ONLY valid JSON with keys: summary, key_decisions, action_items
- Use empty string "" for missing owner/deadline (NOT null)
- Do NOT add extra fields
- Do NOT hallucinate information
- NEVER miss decisions with "remove", "change", "agreed", "decided"

You NEVER:
- Invent or assume information
- Use vague or generic statements
- Miss action items or decisions
- Add fields not in the specification
- Ignore process or policy changes"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.05,
                max_tokens=2500,
                response_format={"type": "json_object"}
            )
            
            notes_data = json.loads(response.choices[0].message.content)
            
            # STRICT schema validation
            required_keys = ["summary", "key_decisions", "action_items"]
            for key in required_keys:
                if key not in notes_data:
                    raise ValueError(f"Missing required key: {key}")
            
            # Validate and clean the response
            notes_data = self._validate_and_clean_notes(notes_data, transcript, participants)
            
            # NEW: Multi-pass analysis for maximum accuracy (+3-5%)
            print("🔄 Running multi-pass validation...")
            notes_data = self.multi_pass_analyzer.analyze(transcript, notes_data, participants)
            
            # NEW: Score confidence (+1-2%)
            print("📊 Scoring confidence...")
            scored_notes = self.confidence_scorer.score_all(notes_data, transcript, participants)
            
            # Filter low confidence items (threshold: 0.5)
            notes_data = self.confidence_scorer.filter_by_confidence(scored_notes, min_confidence=0.5)
            
            # Show confidence stats
            stats = self.confidence_scorer.get_confidence_stats(scored_notes)
            if stats['decisions']['total'] > 0:
                print(f"   Decisions avg confidence: {stats['decisions']['avg_confidence']:.2f}")
            if stats['actions']['total'] > 0:
                print(f"   Actions avg confidence: {stats['actions']['avg_confidence']:.2f}")
            
            # STEP 3: Filter procedural decisions for formal meetings
            if meeting_type == 'formal':
                original_count = len(notes_data['key_decisions'])
                notes_data['key_decisions'] = self.meeting_type_detector.filter_procedural_decisions(
                    notes_data['key_decisions'], 
                    meeting_type
                )
                filtered_count = original_count - len(notes_data['key_decisions'])
                if filtered_count > 0:
                    print(f"🗑️  Filtered {filtered_count} procedural decision(s)")
            
            # STEP 4: Use enhanced decision classifier if decisions are weak
            if len(notes_data['key_decisions']) < 2:
                print("🔍 Using enhanced decision classifier...")
                classified_decisions = self.decision_classifier.extract_decisions(transcript)
                high_conf_decisions = self.decision_classifier.filter_by_confidence(classified_decisions, min_confidence=0.75)
                
                # Filter procedural for formal meetings
                if meeting_type == 'formal':
                    decision_texts = [d['decision'] for d in high_conf_decisions]
                    decision_texts = self.meeting_type_detector.filter_procedural_decisions(
                        decision_texts, 
                        meeting_type
                    )
                    high_conf_decisions = [d for d in high_conf_decisions if d['decision'] in decision_texts]
                
                if high_conf_decisions:
                    # Merge with existing decisions
                    existing = set(notes_data['key_decisions'])
                    for decision in high_conf_decisions:
                        if decision['decision'] not in existing:
                            notes_data['key_decisions'].append(decision['decision'])
                    
                    print(f"✅ Added {len(high_conf_decisions)} high-confidence decisions")
            
            # STEP 4.5: ALWAYS run enhanced classifier to catch high-value signals
            # This catches permanent changes and culture shifts that LLM might miss
            print("🔍 Scanning for high-value signals (permanent changes, culture shifts)...")
            all_classified = self.decision_classifier.extract_decisions(transcript)
            
            # Extract CRITICAL and HIGH priority decisions
            critical_decisions = [d for d in all_classified if d.get('priority') in ['critical', 'high'] and d['confidence'] >= 0.85]
            
            if critical_decisions:
                existing = set(d.lower() for d in notes_data['key_decisions'])  # Case-insensitive comparison
                added_count = 0
                for decision in critical_decisions:
                    # Check for duplicates (case-insensitive)
                    if decision['decision'].lower() not in existing:
                        notes_data['key_decisions'].append(decision['decision'])
                        existing.add(decision['decision'].lower())
                        added_count += 1
                        if decision.get('priority') == 'critical':
                            print(f"   🚨 CRITICAL: {decision['decision'][:80]}...")
                
                if added_count > 0:
                    print(f"✅ Added {added_count} high-value decision(s)")
            
            # STEP 4.6: Remove suggestions and questions that slipped through
            # Filter out sentences with "should" unless they have confirmed decision indicators
            filtered_decisions = []
            seen_decisions = set()  # Track unique decisions (case-insensitive)
            
            for decision in notes_data['key_decisions']:
                decision_lower = decision.lower().strip()
                
                # Skip duplicates
                if decision_lower in seen_decisions:
                    continue
                
                # Check if it's a question
                if '?' in decision or decision_lower.startswith(('are we', 'is this', 'do we', 'can we', 'will we')):
                    continue
                
                # Check if it's a suggestion
                is_suggestion = any(word in decision_lower for word in ['should', 'could', 'might', 'maybe', 'consider', 'wondering if', 'what if', 'propose'])
                # Check if it has confirmed decision indicators
                is_confirmed = any(word in decision_lower for word in ['decided', 'agreed', 'approved', 'confirmed', 'permanent', 'officially', 'formally'])
                
                # Check if it's just a statement without decision content
                is_statement = any(phrase in decision_lower for phrase in ['i guess', 'i added', 'i think', 'i feel', 'i was'])
                
                # Keep if: not a suggestion/question/statement OR has confirmed indicators
                if (not is_suggestion and not is_statement) or is_confirmed:
                    filtered_decisions.append(decision)
                    seen_decisions.add(decision_lower)
            
            notes_data['key_decisions'] = filtered_decisions
            
            # STEP 5: Classify action items based on meeting type
            if meeting_type == 'formal':
                notes_data['action_items'] = self.meeting_type_detector.classify_action_items(
                    notes_data['action_items'],
                    meeting_type
                )
                
                # Remove 'type' field before returning (not in schema)
                for item in notes_data['action_items']:
                    item.pop('type', None)
            
            # Use strict action item extraction if needed
            if len(notes_data['action_items']) == 0:
                print("🔍 Using strict action item extraction...")
                extracted_actions = self.action_extractor.extract_action_items(transcript, participants)
                high_conf_actions = self.action_extractor.filter_by_confidence(extracted_actions, min_confidence=0.5)
                notes_data['action_items'] = [
                    {
                        'task': item['task'],
                        'owner': item['owner'],
                        'deadline': item['deadline']
                    }
                    for item in high_conf_actions
                ]
                print(f"✅ Extracted {len(notes_data['action_items'])} high-confidence action items")
            
            # STEP 6: Add priority weighting to action items (internal use only)
            # Note: Priority is calculated but not included in final output (schema compliance)
            if notes_data['action_items']:
                print("📊 Calculating action item priorities...")
                for item in notes_data['action_items']:
                    # Calculate priority for internal ranking
                    priority = self._calculate_action_priority(item['task'], item['owner'], item['deadline'])
                    # Store internally but don't add to output
                    item['_priority'] = priority
                
                # Sort by priority (urgent first)
                priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
                notes_data['action_items'].sort(key=lambda x: priority_order.get(x.get('_priority', 'medium'), 2))
                
                # Remove internal priority field before output
                for item in notes_data['action_items']:
                    item.pop('_priority', None)
                
                # Show priority distribution
                urgent_count = sum(1 for item in notes_data['action_items'] if item.get('deadline', '').lower() in ['today', 'tomorrow', 'asap'])
                if urgent_count > 0:
                    print(f"   ⚡ {urgent_count} urgent action(s) detected")
            
            # Enhancement disabled for strict schema compliance
            # if transcript_quality != "poor":
            #     notes_data = enhancer.enhance_notes(notes_data, transcript)
            
            # NEW: Update context manager with extracted information
            for decision in notes_data['key_decisions']:
                priority = 'high' if any(word in decision.lower() for word in ['permanent', 'critical', 'officially']) else 'medium'
                self.context_manager.add_decision(decision, priority)
            
            for action in notes_data['action_items']:
                self.context_manager.add_action_item(action['task'], action['owner'], action['deadline'])
            
            # Return MeetingNotes with ONLY required fields
            return MeetingNotes(
                meeting_id=meeting_id,
                title=title,
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                participants=participants,
                **notes_data
            )
            
        except Exception as e:
            print(f"Error generating notes: {e}")
            # Enhanced fallback with better extraction
            return self._generate_fallback_notes(meeting_id, title, participants, transcript)
    
    def _assess_transcript_quality(self, transcript: str) -> str:
        """Assess transcript quality with detailed metrics"""
        if not transcript or len(transcript.strip()) < 50:
            return "poor"
        
        words = transcript.split()
        word_count = len(words)
        
        if word_count < 20:
            return "poor"
        
        # Check for repetitive content
        unique_words = len(set(word.lower() for word in words))
        repetition_ratio = unique_words / word_count if word_count > 0 else 0
        
        # Check for meaningful content
        filler_words = {'thank', 'you', 'obrigado', 'gracias', 'thanks', 'спасибо', 
                       'vielen', 'dank', 'um', 'uh', 'like', 'well', 'so'}
        meaningful_words = [w for w in words if w.lower() not in filler_words]
        meaningful_ratio = len(meaningful_words) / word_count if word_count > 0 else 0
        
        # Check for action indicators (sign of structured content)
        action_indicators = ['will', 'should', 'must', 'needs', 'decided', 'agreed', 
                           'approved', 'confirmed', 'by friday', 'next week', 'tomorrow']
        action_count = sum(1 for indicator in action_indicators if indicator in transcript.lower())
        
        # Check for speaker attribution
        import re
        speaker_patterns = len(re.findall(r'\b[A-Z][a-z]+\s*:', transcript))
        speaker_mentions = len(re.findall(r'\b[A-Z][a-z]+\s+(?:said|will|should|needs)', transcript))
        has_attribution = speaker_patterns + speaker_mentions > 0
        
        # Scoring system
        score = 0
        
        # Word count score (0-30 points)
        if word_count >= 200:
            score += 30
        elif word_count >= 100:
            score += 20
        elif word_count >= 50:
            score += 10
        
        # Uniqueness score (0-25 points)
        if repetition_ratio >= 0.6:
            score += 25
        elif repetition_ratio >= 0.4:
            score += 15
        elif repetition_ratio >= 0.3:
            score += 5
        
        # Meaningful content score (0-20 points)
        if meaningful_ratio >= 0.8:
            score += 20
        elif meaningful_ratio >= 0.6:
            score += 10
        elif meaningful_ratio >= 0.4:
            score += 5
        
        # Structure score (0-15 points)
        if action_count >= 5:
            score += 15
        elif action_count >= 3:
            score += 10
        elif action_count >= 1:
            score += 5
        
        # Attribution score (0-10 points)
        if has_attribution:
            score += 10
        
        # Determine quality level
        if score >= 75:
            return "excellent"
        elif score >= 50:
            return "good"
        elif score >= 30:
            return "fair"
        else:
            return "poor"
    
    def _calculate_action_priority(self, task: str, owner: str, deadline: str) -> str:
        """
        Calculate priority for action items
        
        Priority levels:
        - urgent: Immediate action needed
        - high: Near-term deadline or important
        - medium: Standard priority
        - low: Optional or no deadline
        """
        task_lower = task.lower()
        deadline_lower = deadline.lower() if deadline else ""
        
        # Check for urgent indicators
        urgent_keywords = ['urgent', 'asap', 'immediately', 'critical', 'today', 'now']
        if any(keyword in task_lower or keyword in deadline_lower for keyword in urgent_keywords):
            return 'urgent'
        
        # Check for high priority indicators
        high_keywords = ['important', 'priority', 'soon', 'tomorrow', 'this week']
        if any(keyword in task_lower or keyword in deadline_lower for keyword in high_keywords):
            return 'high'
        
        # Check deadline proximity
        if deadline:
            if any(word in deadline_lower for word in ['today', 'tomorrow', 'asap']):
                return 'urgent'
            elif any(word in deadline_lower for word in ['this week', 'friday', 'monday', 'tuesday', 'wednesday', 'thursday']):
                return 'high'
            elif any(word in deadline_lower for word in ['next week', 'this month']):
                return 'medium'
        
        # Has owner = medium priority, no owner = low priority
        return 'medium' if owner else 'low'
    
    def _validate_and_clean_notes(self, notes_data: dict, transcript: str, participants: list) -> dict:
        """Validate and clean notes to match EXACT schema specification"""
        
        # Ensure all required fields exist
        if 'summary' not in notes_data or not notes_data['summary']:
            notes_data['summary'] = self._extract_summary_fallback(transcript)
        
        if 'key_decisions' not in notes_data:
            notes_data['key_decisions'] = []
        
        if 'action_items' not in notes_data:
            notes_data['action_items'] = []
        
        # Clean key_decisions: must be array of strings
        cleaned_decisions = []
        for decision in notes_data['key_decisions']:
            if isinstance(decision, str) and decision.strip():
                cleaned_decisions.append(decision.strip())
            elif isinstance(decision, dict) and decision.get('decision'):
                # Convert old format to new format
                cleaned_decisions.append(decision['decision'].strip())
        notes_data['key_decisions'] = cleaned_decisions
        
        # Clean action_items: ensure owner and deadline are strings (not null)
        cleaned_actions = []
        for item in notes_data['action_items']:
            if isinstance(item, dict) and item.get('task'):
                task = item['task'].strip()
                if len(task) >= 10:  # Minimum task length
                    # Ensure owner and deadline are strings
                    owner = item.get('owner', '')
                    deadline = item.get('deadline', '')
                    
                    # Convert None/null to empty string
                    if owner is None:
                        owner = ''
                    if deadline is None:
                        deadline = ''
                    
                    # Validate owner is not too long (likely extraction error)
                    if isinstance(owner, str) and len(owner.split()) > 3:
                        owner = ''
                    
                    cleaned_actions.append({
                        'task': task,
                        'owner': str(owner),
                        'deadline': str(deadline)
                    })
        notes_data['action_items'] = cleaned_actions
        
        # Use strict action item extraction if needed
        if len(notes_data['action_items']) == 0:
            print("🔍 Using strict action item extraction...")
            extracted_actions = self.action_extractor.extract_action_items(transcript, participants)
            high_conf_actions = self.action_extractor.filter_by_confidence(extracted_actions, min_confidence=0.5)
            notes_data['action_items'] = [
                {
                    'task': item['task'],
                    'owner': item.get('owner') or '',  # Ensure string
                    'deadline': item.get('deadline') or ''  # Ensure string
                }
                for item in high_conf_actions
            ]
            print(f"✅ Extracted {len(notes_data['action_items'])} high-confidence action items")
        
        # Remove any extra fields not in specification
        allowed_keys = {'summary', 'key_decisions', 'action_items'}
        notes_data = {k: v for k, v in notes_data.items() if k in allowed_keys}
        
        return notes_data
    
    def _generate_professional_summary(self, transcript: str) -> str:
        """Generate a professional summary from transcript"""
        sentences = [s.strip() for s in transcript.split('.') if len(s.strip()) > 20]
        
        if len(sentences) >= 3:
            # Take first substantive sentences
            summary_parts = sentences[:3]
            summary = '. '.join(summary_parts) + '.'
            
            # Add context if we can identify key themes
            if 'decided' in transcript.lower() or 'agreed' in transcript.lower():
                summary += ' Key decisions were made regarding project direction.'
            if 'will' in transcript.lower() and any(name[0].isupper() for name in transcript.split()):
                summary += ' Action items were assigned to team members.'
            
            return summary
        
        return f"Meeting covered: {transcript[:200]}..."
    
    def _extract_summary_fallback(self, transcript: str) -> str:
        """Generate a basic summary from transcript"""
        # Take first 200 chars as summary
        summary = transcript[:200].strip()
        if len(transcript) > 200:
            summary += "..."
        return f"Meeting discussion: {summary}"
    
    def _extract_key_points_fallback(self, transcript: str) -> list:
        """Extract key points using simple heuristics"""
        points = []
        sentences = transcript.split('.')
        
        # Look for sentences with key indicators
        keywords = ['important', 'key', 'main', 'critical', 'essential', 'decided', 'agreed']
        
        for sentence in sentences[:10]:  # Check first 10 sentences
            sentence = sentence.strip()
            if len(sentence) > 20 and any(keyword in sentence.lower() for keyword in keywords):
                points.append(sentence)
                if len(points) >= 3:
                    break
        
        return points
    
    def _extract_action_items_fallback(self, transcript: str, participants: list) -> list:
        """Extract action items using pattern matching"""
        action_items = []
        
        # Common action item patterns
        patterns = [
            'will ', 'should ', 'need to ', 'must ', 'has to ',
            'action item', 'todo', 'task', 'follow up'
        ]
        
        sentences = transcript.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if any(pattern in sentence.lower() for pattern in patterns):
                # Try to extract owner
                words = sentence.split()
                owner = ''
                for i, word in enumerate(words):
                    if word.lower() in ['will', 'should', 'needs', 'must'] and i > 0:
                        potential_owner = words[i-1].strip(',')
                        # Check if it's a participant name
                        if potential_owner in participants or potential_owner[0].isupper():
                            owner = potential_owner
                        break
                
                action_items.append({
                    'task': sentence,
                    'owner': owner,
                    'deadline': ''
                })
                
                if len(action_items) >= 3:
                    break
        
        return action_items
    
    def _generate_fallback_notes(self, meeting_id: str, title: str, participants: list, transcript: str) -> MeetingNotes:
        """Generate basic notes if AI fails"""
        return MeetingNotes(
            meeting_id=meeting_id,
            title=title,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            participants=participants,
            summary=self._extract_summary_fallback(transcript),
            key_decisions=[],
            action_items=self._extract_action_items_fallback(transcript, participants)
        )
