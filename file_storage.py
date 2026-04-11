"""
Simple file-based storage for meeting notes
"""
import json
import os
from datetime import datetime
from typing import Optional, List

class FileStorage:
    def __init__(self, storage_dir: str = "meeting_notes"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        print(f"✅ Using file storage: {os.path.abspath(storage_dir)}")
    
    def save_meeting(self, meeting_data: dict):
        """Save meeting to JSON file"""
        meeting_id = meeting_data['meeting_id']
        filename = f"{meeting_id}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        meeting_data['saved_at'] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(meeting_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Meeting saved: {filepath}")
    
    def get_meeting(self, meeting_id: str) -> Optional[dict]:
        """Retrieve meeting by ID"""
        filename = f"{meeting_id}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_all_meetings(self, limit: int = 50) -> List[dict]:
        """Get all meetings (most recent first)"""
        meetings = []
        
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.storage_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    meetings.append(json.load(f))
        
        # Sort by saved_at or date
        meetings.sort(
            key=lambda x: x.get('saved_at', x.get('date', '')),
            reverse=True
        )
        
        return meetings[:limit]
    
    def search_meetings(self, query: str) -> List[dict]:
        """Search meetings by title or content"""
        results = []
        query_lower = query.lower()
        
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.storage_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    meeting = json.load(f)
                    
                    # Search in title and summary
                    if (query_lower in meeting.get('title', '').lower() or
                        query_lower in meeting.get('summary', '').lower()):
                        results.append(meeting)
        
        return results
    
    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete meeting by ID"""
        filename = f"{meeting_id}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"🗑️ Meeting deleted: {meeting_id}")
            return True
        
        return False
    
    def get_stats(self) -> dict:
        """Get storage statistics"""
        files = [f for f in os.listdir(self.storage_dir) if f.endswith('.json')]
        
        return {
            'total_meetings': len(files),
            'storage_type': 'File-based',
            'storage_path': os.path.abspath(self.storage_dir)
        }
    
    def export_meeting_txt(self, meeting_id: str) -> Optional[str]:
        """Export meeting to readable text file with speaker analysis"""
        meeting = self.get_meeting(meeting_id)
        if not meeting:
            return None
        
        notes = meeting.get('notes', meeting)
        
        txt_content = f"""
{'='*70}
MEETING NOTES
{'='*70}

Meeting ID: {notes.get('meeting_id', 'N/A')}
Title: {notes.get('title', 'N/A')}
Date: {notes.get('date', 'N/A')}
Participants: {', '.join(notes.get('participants', []))}

{'='*70}
MINUTES OF MEETING (MoM)
{'='*70}

{notes.get('summary', 'N/A')}

{'='*70}
KEY POINTS
{'='*70}

"""
        for i, point in enumerate(notes.get('key_decisions', []), 1):
            txt_content += f"{i}. {point}\n"
        
        txt_content += f"""
{'='*70}
ACTION ITEMS
{'='*70}

"""
        action_items = notes.get('action_items', [])
        if action_items:
            for i, item in enumerate(action_items, 1):
                txt_content += f"{i}. {item.get('task', 'N/A')}\n"
                owner = item.get('owner', '')
                deadline = item.get('deadline', '')
                txt_content += f"   Owner: {owner if owner else 'Unassigned'}\n"
                txt_content += f"   Deadline: {deadline if deadline else 'No deadline'}\n\n"
        else:
            txt_content += "(No action items identified)\n\n"
        
        txt_content += f"{'='*70}\n"
        
        # Save to file
        txt_filename = f"{meeting_id}.txt"
        txt_filepath = os.path.join(self.storage_dir, txt_filename)
        
        with open(txt_filepath, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        print(f"📄 Text export saved: {txt_filepath}")
        return txt_filepath


# Initialize file storage
storage = FileStorage()
