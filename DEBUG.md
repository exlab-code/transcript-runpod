# 🐛 RunPod Transcription Debugging Guide

This guide helps you debug the transcription endpoint locally instead of waiting 20 minutes for RunPod deployments.

## 🚀 Quick Local Testing

### Option 1: Direct Handler Test (Fastest - 30 seconds)
```bash
# Test the handler logic directly
python3 rp_handler.py --test_input test_input.json

# Or with JSON string
python3 rp_handler.py --test_input '{"input": {"audio_b64": "...", "session_id": "test", "chunk_index": 0}}'
```

### Option 2: Local HTTP Server
```bash
# Start local server
python3 rp_handler.py --rp_serve_api --rp_api_port 8080

# Test with curl in another terminal
curl -X POST http://localhost:8080/run \
     -H "Content-Type: application/json" \
     -d @test_input.json
```

### Option 3: Docker Testing (Most Accurate - 2-5 minutes)
```bash
# Run the automated Docker test
./docker_test.sh

# Or manually:
docker build -t transcript-runpod-test .
docker run --gpus all --rm -v "$(pwd)/test_input.json:/test_input.json" \
    transcript-runpod-test python3 rp_handler.py --test_input /test_input.json
```

## 🔍 Current Issue: cuDNN Library Missing

**Problem**: `libcudnn_ops_infer.so.8: cannot open shared object file`

**Root Cause**: RunPod base image missing complete cuDNN installation

**Current Fix Applied**:
- Install `nvidia-cudnn-cu12==8.9.2.26` via pip
- Set `LD_LIBRARY_PATH` to include pip-installed cuDNN

## 🧪 Test Results Expected

### ✅ Success Case:
```
🚀 Loading faster-whisper model: medium with float16 precision on GPU
✅ Faster-whisper GPU model loaded successfully
🎙️ Processing [test:0] via GPU serverless
📦 Decoded audio: 448840 bytes
Processing audio with duration 00:14.025
VAD filter removed 00:01.073 of audio
✅ [test:0] GPU RTF: 0.05 | 12 segments
```

### ❌ Current Error:
```
Could not load library libcudnn_ops_infer.so.8. Error: libcudnn_ops_infer.so.8: cannot open shared object file: No such file or directory
```

## 🔧 Debug Steps

1. **Test locally first**: `./docker_test.sh`
2. **If local Docker works**: Deploy to RunPod
3. **If local Docker fails**: Fix library paths
4. **Never deploy without local success**

## 📊 Time Savings

- **Old way**: 20 min deploy → test → fail → repeat
- **New way**: 2 min local test → fix → deploy once ✅

## 🎯 Alternative Fixes to Try

If current cuDNN fix doesn't work:

### Fix 1: Use conda cuDNN
```dockerfile
RUN conda install -c conda-forge cudnn=8.9.2
```

### Fix 2: System cuDNN install
```dockerfile
RUN apt-get update && apt-get install -y libcudnn8=8.9.2*
```

### Fix 3: CPU fallback for testing
```python
# In handler, change:
device = "cpu" if os.getenv("USE_CPU_FALLBACK") else "cuda"
```

This way you can test transcription logic without GPU issues.