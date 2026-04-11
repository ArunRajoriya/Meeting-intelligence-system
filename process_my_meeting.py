"""
Simple script to process your meeting recording
Just change the settings below and run!
"""
from simple_meeting_client import MeetingClient

# ============================================
# CHANGE THESE FOR YOUR MEETING
# ============================================
MEETING_TITLE = "Team Standup"
PARTICIPANTS = ["Alice", "Bob", "Charlie"]
AUDIO_FILE = "Summary.mp3"  # Your recording file path

# ============================================
# PROCESS MEETING (Don't change below)
# ============================================
print(f"📝 Processing meeting: {MEETING_TITLE}")
print(f"👥 Participants: {', '.join(PARTICIPANTS)}")
print(f"🎤 Audio file: {AUDIO_FILE}\n")

client = MeetingClient()

# Start meeting
print("1. Starting meeting session...")
client.start_meeting(MEETING_TITLE, PARTICIPANTS)

# Upload audio
print("2. Uploading and transcribing audio...")
client.add_audio(AUDIO_FILE)

# Generate insights
print("3. Generating AI insights...\n")
notes = client.end_meeting()

# Done!
print("\n" + "="*70)
print("✅ SUCCESS! Your meeting notes are ready!")
print("="*70)
print(f"\n📄 Text file: meeting_notes/{notes['meeting_id']}.txt")
print(f"📊 JSON file: meeting_notes/{notes['meeting_id']}.json")
print("\nYou can now:")
print("  - Open the .txt file to read notes")
print("  - Email the files to participants")
print("  - Search meetings: http://localhost:8000/meetings")
print("\n" + "="*70)
