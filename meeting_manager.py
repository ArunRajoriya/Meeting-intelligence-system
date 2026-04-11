from schemas import MeetingStatus, MeetingNotes
from datetime import datetime
import uuid
from file_storage import storage

class MeetingSession:
    def __init__(self, meeting_id: str, title: str, participants: list):
        self.meeting_id = meeting_id
        self.title = title
        self.participants = participants
        self.status = MeetingStatus.RECORDING
        self.transcript = ""
        self.started_at = datetime.now().isoformat()
        self.notes: MeetingNotes | None = None
    
    def add_transcript(self, text: str):
        """Append text to ongoing transcript"""
        if self.transcript:
            self.transcript += " " + text
        else:
            self.transcript = text
    
    def get_transcript_length(self) -> int:
        return len(self.transcript)
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        data = {
            'meeting_id': self.meeting_id,
            'title': self.title,
            'participants': self.participants,
            'status': self.status,
            'transcript': self.transcript,
            'started_at': self.started_at
        }
        if self.notes:
            data['notes'] = self.notes.model_dump()
        return data

class MeetingManager:
    def __init__(self):
        self.active_meeting: MeetingSession | None = None
    
    def start_meeting(self, title: str, participants: list) -> MeetingSession:
        """Start a new meeting session"""
        if self.active_meeting:
            raise ValueError("A meeting is already in progress. Stop it first.")
        
        meeting_id = str(uuid.uuid4())[:8]
        session = MeetingSession(meeting_id, title, participants)
        self.active_meeting = session
        return session
    
    def add_input(self, text: str):
        """Add transcript input to active meeting"""
        if not self.active_meeting:
            raise ValueError("No active meeting. Start a meeting first.")
        
        if self.active_meeting.status != MeetingStatus.RECORDING:
            raise ValueError("Meeting is not in recording state.")
        
        self.active_meeting.add_transcript(text)
    
    def get_active_meeting(self) -> MeetingSession | None:
        return self.active_meeting
    
    def stop_meeting(self) -> MeetingSession:
        """Stop the active meeting"""
        if not self.active_meeting:
            raise ValueError("No active meeting to stop.")
        
        self.active_meeting.status = MeetingStatus.PROCESSING
        return self.active_meeting
    
    def complete_meeting(self, notes: MeetingNotes):
        """Mark meeting as completed and save to file"""
        if not self.active_meeting:
            raise ValueError("No active meeting.")
        
        self.active_meeting.notes = notes
        self.active_meeting.status = MeetingStatus.COMPLETED
        
        # Save to file storage
        storage.save_meeting(self.active_meeting.to_dict())
        
        # Also export as readable text
        storage.export_meeting_txt(self.active_meeting.meeting_id)
        
        self.active_meeting = None
    
    def get_meeting(self, meeting_id: str) -> dict | None:
        """Retrieve meeting from file storage"""
        return storage.get_meeting(meeting_id)
    
    def get_all_meetings(self, limit: int = 50) -> list:
        """Get all meetings from file storage"""
        return storage.get_all_meetings(limit)
    
    def search_meetings(self, query: str) -> list:
        """Search meetings by title or content"""
        return storage.search_meetings(query)
    
    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete meeting from file storage"""
        return storage.delete_meeting(meeting_id)

meeting_manager = MeetingManager()
