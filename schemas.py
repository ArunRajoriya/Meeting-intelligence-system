from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from enum import Enum

class MeetingStatus(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"

class ActionItem(BaseModel):
    task: str
    owner: str = ""  # Empty string if not found (not null)
    deadline: str = ""  # Empty string if not found (not null)

class MeetingNotes(BaseModel):
    meeting_id: str
    title: str
    date: str
    participants: List[str] = []
    summary: str = Field(description="Minutes of Meeting (MoM)")
    key_decisions: List[str] = Field(default_factory=list, description="Key decisions made")
    action_items: List[ActionItem] = Field(default_factory=list, description="Action items with owners and deadlines")

class TranscriptInput(BaseModel):
    text: str

class MeetingStartRequest(BaseModel):
    title: str = "Meeting"
    participants: List[str] = []

class MeetingStatusResponse(BaseModel):
    meeting_id: str
    status: MeetingStatus
    transcript_length: int
    started_at: str | None = None

class TranscriptionResponse(BaseModel):
    transcript: str
    duration: float

class InsightsResponse(BaseModel):
    insights: MeetingNotes
    transcript: str

# Chat/Conversation Schemas
class ChatRequest(BaseModel):
    message: str
    include_meeting_context: bool = False

class ChatResponse(BaseModel):
    user_message: str
    assistant_reply: str
    audio_available: bool = True

class VoiceChatResponse(BaseModel):
    transcribed_text: str
    assistant_reply: str
    audio_url: str
