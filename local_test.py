#!/usr/bin/env python3
"""
Local testing script for RunPod transcription handler
This tests the core logic without requiring RunPod dependencies
"""

import json
import base64
import tempfile
import os
from datetime import datetime

# Mock the runpod import for local testing
class MockRunPod:
    class serverless:
        @staticmethod
        def start(config):
            print("Mock RunPod serverless started")

# Replace the import
import sys
sys.modules['runpod'] = MockRunPod

# Test the cuDNN/CUDA detection
def test_cuda_setup():
    """Test if CUDA and cuDNN are properly set up"""
    try:
        import torch
        print(f"✅ PyTorch imported successfully")
        print(f"CUDA available: {torch.cuda.is_available()}")
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Device count: {torch.cuda.device_count()}")
        if torch.cuda.is_available():
            print(f"Device name: {torch.cuda.get_device_name(0)}")
    except ImportError as e:
        print(f"❌ PyTorch not available: {e}")
        return False
    
    # Test faster-whisper with CUDA
    try:
        from faster_whisper import WhisperModel
        print(f"✅ faster-whisper imported successfully")
        
        # Try to create a CUDA model (this is where cuDNN issues would show up)
        print("🧪 Testing CUDA model creation...")
        model = WhisperModel("tiny", device="cuda", compute_type="float16")
        print("✅ CUDA Whisper model created successfully!")
        
        # Test actual transcription with dummy audio
        print("🧪 Testing transcription with dummy audio...")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            # Create minimal WAV file (44 bytes header + some silence)
            wav_header = base64.b64decode("UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=")
            temp_file.write(wav_header)
            temp_path = temp_file.name
        
        try:
            segments, info = model.transcribe(temp_path)
            segments_list = list(segments)
            print(f"✅ Transcription successful! Found {len(segments_list)} segments")
            print(f"Audio duration: {info.duration:.2f}s")
            return True
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            if "libcudnn" in str(e):
                print("🔍 This is the cuDNN library issue we need to fix!")
            return False
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
                
    except ImportError as e:
        print(f"❌ faster-whisper not available: {e}")
        return False
    except Exception as e:
        print(f"❌ CUDA model creation failed: {e}")
        if "libcudnn" in str(e):
            print("🔍 This is the cuDNN library issue we need to fix!")
        return False

def main():
    print("🚀 RunPod Transcription Handler - Local Test")
    print("=" * 50)
    
    # Test CUDA/cuDNN setup
    print("\n1. Testing CUDA/cuDNN setup...")
    cuda_works = test_cuda_setup()
    
    if cuda_works:
        print("\n✅ All tests passed! The handler should work on RunPod.")
    else:
        print("\n❌ Tests failed. The cuDNN library issue needs to be fixed.")
        print("\n🔧 Suggested fixes:")
        print("- Install cuDNN: pip install nvidia-cudnn-cu12")
        print("- Set LD_LIBRARY_PATH to include cuDNN libraries")
        print("- Use CPU fallback for local testing")

if __name__ == "__main__":
    main()