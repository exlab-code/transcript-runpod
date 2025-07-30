# RunPod GPU Transcription Worker

⚡ Fast GPU transcription using faster-whisper on RunPod serverless.

## Quick Deploy

1. **Create RunPod Endpoint**: Serverless → New Endpoint
2. **GitHub Integration**: Select this repository 
3. **GPU**: RTX 4090 or RTX 3080
4. **Environment Variables**:
   - `WHISPER_MODEL=medium`
   - `WHISPER_COMPUTE_TYPE=float16`

## Test

```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d @test_input.json
```

## Performance

- **RTF**: 0.02-0.05 (20x faster than real-time)
- **2-minute audio**: ~2-6 seconds processing
- **Cold start**: ~10-30 seconds

## Files

- `rp_handler.py` - Main transcription handler
- `requirements.txt` - Minimal dependencies  
- `Dockerfile` - Container setup
- `test_input.json` - Test payload