"""
Quick test to verify backend is working
"""
import requests
import time

API_URL = "http://localhost:8000"

def test_backend():
    print("="*60)
    print("🧪 Testing Backend API")
    print("="*60)
    
    try:
        # Test 1: Health check
        print("\n1️⃣  Testing health endpoint...")
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return
        
        # Test 2: Root endpoint
        print("\n2️⃣  Testing root endpoint...")
        response = requests.get(f"{API_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ System status: {data.get('status')}")
            print(f"   ✅ Features: {len(data.get('features', []))} available")
        else:
            print(f"   ❌ Root endpoint failed: {response.status_code}")
            return
        
        # Test 3: Start meeting
        print("\n3️⃣  Testing start meeting...")
        response = requests.post(f"{API_URL}/meeting/start", json={
            "title": "Test Meeting",
            "participants": ["Alice", "Bob"]
        })
        if response.status_code == 200:
            data = response.json()
            meeting_id = data.get('meeting_id')
            print(f"   ✅ Meeting started: {meeting_id}")
            
            # Test 4: Add input
            print("\n4️⃣  Testing add input...")
            response = requests.post(f"{API_URL}/meeting/input", json={
                "text": "We decided to use React for the frontend. Alice will set up the project by Friday."
            })
            if response.status_code == 200:
                print("   ✅ Input added successfully")
            else:
                print(f"   ❌ Add input failed: {response.status_code}")
            
            # Test 5: Stop meeting
            print("\n5️⃣  Testing stop meeting (generating notes)...")
            response = requests.post(f"{API_URL}/meeting/stop")
            if response.status_code == 200:
                notes = response.json()
                print("   ✅ Meeting stopped and notes generated")
                print(f"   📝 Summary: {notes.get('summary', '')[:100]}...")
                print(f"   ✅ Key decisions: {len(notes.get('key_decisions', []))}")
                print(f"   ✅ Action items: {len(notes.get('action_items', []))}")
            else:
                print(f"   ❌ Stop meeting failed: {response.status_code}")
        else:
            print(f"   ❌ Start meeting failed: {response.status_code}")
        
        print("\n" + "="*60)
        print("✅ All tests passed! Backend is working correctly")
        print("="*60)
        print("\n🚀 Ready to start frontend!")
        print("   Run: cd frontend && npm run dev")
        print("   Or:  start_fullstack.bat")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to backend!")
        print("   Please start the backend first:")
        print("   python main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    print("\n⏳ Waiting for server to start...")
    time.sleep(2)
    test_backend()
