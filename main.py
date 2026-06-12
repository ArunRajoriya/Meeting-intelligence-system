from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from ai_service import AIService
from meeting_manager import meeting_manager
from file_storage import storage
from schemas import (
    MeetingStartRequest, MeetingStatusResponse, TranscriptInput,
    MeetingNotes, TranscriptionResponse, ChatRequest, ChatResponse, VoiceChatResponse
)
import tempfile
import os

app = FastAPI(
    title="Meeting Intelligence System",
    description="Capture meeting data and generate structured insights (Notes, MoM, Action Items)",
    version="2.0.0"
)

ai_service = AIService()

@app.get("/")
def root():
    stats = storage.get_stats()
    return {
        "message": "Meeting Intelligence System",
        "status": "active",
        "features": [
            "Real-time capture",
            "Voice-to-text (Groq Whisper)",
            "Text-to-voice (gTTS)",
            "Conversational AI",
            "MoM generation",
            "File-based storage"
        ],
        "storage": stats
    }

# ========== CONVERSATIONAL AI ENDPOINTS ==========

@app.post("/chat", response_model=ChatResponse)
def chat_with_ai(request: ChatRequest):
    """💬 Chat with AI assistant (text-based conversation)"""
    try:
        # Get meeting context if requested
        context = None
        if request.include_meeting_context:
            session = meeting_manager.get_active_meeting()
            if session and session.transcript:
                context = session.transcript
        
        reply = ai_service.chat(request.message, context)
        
        return ChatResponse(
            user_message=request.message,
            assistant_reply=reply,
            audio_available=True
        )
    except Exception as e:
        raise HTTPException(500, f"Chat failed: {str(e)}")

@app.post("/chat/voice", response_model=VoiceChatResponse)
async def voice_chat(audio: UploadFile = File(...)):
    """🎤 Voice conversation: Send audio, get text + voice response
    
    1. Transcribes your voice to text (Groq Whisper)
    2. AI generates response (Groq LLaMA)
    3. Converts response to speech (gTTS)
    """
    if not audio.content_type.startswith("audio/"):
        raise HTTPException(400, "File must be audio format")
    
    try:
        # Step 1: Voice to Text (Groq Whisper)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        with open(tmp_path, "rb") as audio_file:
            user_text, _ = ai_service.transcribe_audio(audio_file)
        
        os.unlink(tmp_path)
        
        # Step 2: Get AI response (Groq LLaMA)
        context = None
        session = meeting_manager.get_active_meeting()
        if session and session.transcript:
            context = session.transcript
        
        assistant_reply = ai_service.chat(user_text, context)
        
        # Step 3: Text to Speech (gTTS)
        audio_path = ai_service.text_to_speech(assistant_reply)
        
        return VoiceChatResponse(
            transcribed_text=user_text,
            assistant_reply=assistant_reply,
            audio_url=f"/audio/{os.path.basename(audio_path)}"
        )
    
    except Exception as e:
        raise HTTPException(500, f"Voice chat failed: {str(e)}")

@app.get("/audio/{filename}")
def get_audio(filename: str):
    """🔊 Download generated audio response"""
    audio_path = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.exists(audio_path):
        raise HTTPException(404, "Audio file not found")
    
    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename=filename
    )

@app.post("/chat/reset")
def reset_conversation():
    """🔄 Reset conversation history"""
    ai_service.reset_conversation()
    return {"message": "Conversation history cleared"}

@app.post("/chat/tts")
def text_to_speech_endpoint(text: str):
    """🔊 Convert any text to speech"""
    try:
        audio_path = ai_service.text_to_speech(text)
        return {
            "message": "Audio generated",
            "audio_url": f"/audio/{os.path.basename(audio_path)}"
        }
    except Exception as e:
        raise HTTPException(500, f"TTS failed: {str(e)}")

# ========== MEETING CONTROL ENDPOINTS ==========

@app.post("/meeting/start", response_model=MeetingStatusResponse)
def start_meeting(request: MeetingStartRequest):
    """🟢 START capturing meeting - Turn the system ON"""
    try:
        session = meeting_manager.start_meeting(request.title, request.participants)
        return MeetingStatusResponse(
            meeting_id=session.meeting_id,
            status=session.status,
            transcript_length=0,
            started_at=session.started_at
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/meeting/input")
def add_meeting_input(input_data: TranscriptInput):
    """📝 Add transcript input to active meeting (simulated text input)"""
    try:
        meeting_manager.add_input(input_data.text)
        session = meeting_manager.get_active_meeting()
        return {
            "message": "Input added",
            "meeting_id": session.meeting_id,
            "transcript_length": session.get_transcript_length()
        }
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/meeting/input/audio")
async def add_audio_input(audio: UploadFile = File(...)):
    """🎤 Add audio input to active meeting (transcribed automatically via Groq Whisper)"""
    if not audio.content_type.startswith("audio/"):
        raise HTTPException(400, "File must be audio format")
    
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Transcribe
        try:
            with open(tmp_path, "rb") as audio_file:
                transcript, _ = ai_service.transcribe_audio(audio_file, filename="chunk.wav")
        finally:
            # Always cleanup temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        # Add to meeting
        meeting_manager.add_input(transcript)
        session = meeting_manager.get_active_meeting()
        
        return {
            "message": "Audio transcribed and added",
            "meeting_id": session.meeting_id,
            "transcript": transcript,
            "transcript_length": session.get_transcript_length()
        }
    except ValueError as e:
        print(f"❌ ValueError: {e}")
        raise HTTPException(400, str(e))
    except Exception as e:
        print(f"❌ Exception in audio processing: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Audio processing failed: {str(e)}")

@app.get("/meeting/status", response_model=MeetingStatusResponse)
def get_meeting_status():
    """📊 Get current meeting status"""
    session = meeting_manager.get_active_meeting()
    if not session:
        raise HTTPException(404, "No active meeting")
    
    return MeetingStatusResponse(
        meeting_id=session.meeting_id,
        status=session.status,
        transcript_length=session.get_transcript_length(),
        started_at=session.started_at
    )

@app.post("/meeting/stop", response_model=MeetingNotes)
def stop_meeting():
    """🔴 STOP meeting and generate insights (Notes, MoM, Decisions, Action Items)"""
    try:
        session = meeting_manager.stop_meeting()
        
        if not session.transcript:
            raise HTTPException(400, "No transcript data captured")
        
        # Generate comprehensive meeting notes
        notes = ai_service.generate_meeting_notes(
            session.transcript,
            session.meeting_id,
            session.title,
            session.participants
        )
        
        meeting_manager.complete_meeting(notes)
        
        return notes
    
    except ValueError as e:
        print(f"❌ ValueError in stop_meeting: {e}")
        raise HTTPException(400, str(e))
    except Exception as e:
        print(f"❌ Exception in stop_meeting: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to generate notes: {str(e)}")

@app.post("/meeting/reset")
def reset_meeting():
    """🔄 Force reset/clear any stuck meeting session"""
    try:
        meeting_manager.force_reset()
        return {"message": "Meeting session reset successfully"}
    except Exception as e:
        raise HTTPException(500, f"Reset failed: {str(e)}")

@app.get("/meeting/{meeting_id}")
def get_meeting_notes(meeting_id: str):
    """📄 Retrieve meeting notes by ID"""
    meeting = meeting_manager.get_meeting(meeting_id)
    if not meeting or 'notes' not in meeting:
        raise HTTPException(404, "Meeting not found or not completed")
    
    return meeting['notes']

# ========== FILE STORAGE ENDPOINTS ==========

@app.get("/meetings")
def get_all_meetings(limit: int = 50):
    """📚 Get all saved meetings"""
    return storage.get_all_meetings(limit)

@app.get("/meetings/search")
def search_meetings(query: str):
    """🔍 Search meetings by title or content"""
    return storage.search_meetings(query)

@app.delete("/meeting/{meeting_id}/delete")
def delete_meeting(meeting_id: str):
    """🗑️ Delete a meeting"""
    success = storage.delete_meeting(meeting_id)
    if success:
        return {"message": "Meeting deleted"}
    raise HTTPException(404, "Meeting not found")

@app.get("/meeting/{meeting_id}/export")
def export_meeting_txt(meeting_id: str):
    """📄 Export meeting as text file"""
    filepath = storage.export_meeting_txt(meeting_id)
    if not filepath:
        raise HTTPException(404, "Meeting not found")
    
    return FileResponse(
        filepath,
        media_type="text/plain",
        filename=f"meeting_{meeting_id}.txt"
    )

@app.get("/stats")
def get_stats():
    """📊 Get storage statistics"""
    return storage.get_stats()

# ========== LEGACY ENDPOINTS ==========

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio file to text using Groq Whisper"""
    if not audio.content_type.startswith("audio/"):
        raise HTTPException(400, "File must be audio format")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        with open(tmp_path, "rb") as audio_file:
            transcript, duration = ai_service.transcribe_audio(audio_file)
        
        os.unlink(tmp_path)
        
        return TranscriptionResponse(transcript=transcript, duration=duration)
    
    except Exception as e:
        raise HTTPException(500, f"Transcription failed: {str(e)}")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "meeting-intelligence",
        "storage": storage.get_stats()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
