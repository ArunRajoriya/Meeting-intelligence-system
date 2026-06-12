"""
Test Microphone - Diagnostic Tool
Helps identify why microphone isn't capturing audio
"""
import pyaudio
import numpy as np
import time

def test_microphone():
    print("="*70)
    print("🎤 MICROPHONE DIAGNOSTIC TEST")
    print("="*70)
    
    audio = pyaudio.PyAudio()
    
    # List all input devices
    print("\n📋 Available Input Devices:")
    print("-"*70)
    
    input_devices = []
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            input_devices.append((i, info))
            marker = "🎤" if 'mic' in info['name'].lower() else "🔊"
            print(f"{i}: {marker} {info['name']}")
            print(f"   Channels: {info['maxInputChannels']}, Rate: {info['defaultSampleRate']}")
    
    if not input_devices:
        print("\n❌ No input devices found!")
        audio.terminate()
        return
    
    print("\n" + "="*70)
    device_choice = input("Select device number to test (or press Enter for default): ").strip()
    
    if device_choice.isdigit():
        device_index = int(device_choice)
    else:
        device_index = None
        print("Using default input device")
    
    # Test the device
    print("\n" + "="*70)
    print("🧪 TESTING MICROPHONE")
    print("="*70)
    print("\n🎤 Speak into your microphone NOW...")
    print("   (Testing for 5 seconds)\n")
    
    try:
        # Open stream
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=1024
        )
        
        max_level = 0
        levels = []
        
        # Record for 5 seconds
        for i in range(50):  # 50 chunks = ~5 seconds
            try:
                data = stream.read(1024, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                level = np.abs(audio_data).mean()
                levels.append(level)
                max_level = max(max_level, level)
                
                # Show live level
                bars = int(level / 100)
                bar_display = "█" * min(bars, 50)
                print(f"\r   Level: [{bar_display:<50}] {level:.0f}   ", end="", flush=True)
                
                time.sleep(0.1)
            except Exception as e:
                print(f"\n❌ Error reading: {e}")
                break
        
        stream.stop_stream()
        stream.close()
        
        # Results
        print("\n\n" + "="*70)
        print("📊 TEST RESULTS")
        print("="*70)
        
        avg_level = np.mean(levels) if levels else 0
        
        print(f"\n   Maximum Level: {max_level:.0f}")
        print(f"   Average Level: {avg_level:.0f}")
        
        if max_level > 1000:
            print("\n   ✅ EXCELLENT: Microphone is working great!")
        elif max_level > 500:
            print("\n   ✅ GOOD: Microphone is working")
            print("   💡 Consider speaking louder or increasing mic volume")
        elif max_level > 100:
            print("\n   ⚠️  WEAK: Microphone is too quiet")
            print("   💡 SOLUTION:")
            print("      1. Increase microphone volume in Windows to 100%")
            print("      2. Enable 'Microphone Boost' (+20dB or +30dB)")
            print("      3. Speak closer to the microphone")
        elif max_level > 10:
            print("\n   ❌ VERY WEAK: Microphone barely working")
            print("   💡 SOLUTION:")
            print("      1. Check if microphone is muted")
            print("      2. Check if correct microphone is selected")
            print("      3. Increase volume to 100% + enable boost")
        else:
            print("\n   ❌ NOT WORKING: No audio detected")
            print("   💡 SOLUTION:")
            print("      1. Check if microphone is plugged in")
            print("      2. Check if microphone is muted (hardware switch)")
            print("      3. Try a different microphone")
            print("      4. Check Windows Privacy Settings:")
            print("         Settings → Privacy → Microphone → Allow apps to access")
        
        print("\n" + "="*70)
        print("💡 HOW TO FIX LOW MICROPHONE VOLUME:")
        print("="*70)
        print("\n1. Right-click speaker icon → 'Sounds'")
        print("2. 'Recording' tab → Select your microphone")
        print("3. Click 'Properties'")
        print("4. 'Levels' tab:")
        print("   - Set 'Microphone' to 100")
        print("   - Set 'Microphone Boost' to +20dB or +30dB (if available)")
        print("5. Click 'OK' and test again")
        
    except Exception as e:
        print(f"\n\n❌ Failed to open microphone: {e}")
        print("\n💡 Possible issues:")
        print("   1. Microphone is being used by another application")
        print("   2. Microphone permissions not granted")
        print("   3. Audio driver issue")
    
    audio.terminate()
    print("\n" + "="*70)

if __name__ == "__main__":
    test_microphone()
