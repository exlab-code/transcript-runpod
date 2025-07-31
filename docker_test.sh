#!/bin/bash

echo "🐳 RunPod Docker Local Testing Script"
echo "====================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"

# Build the image
echo ""
echo "🔨 Building Docker image..."
docker build -t transcript-runpod-test . || {
    echo "❌ Docker build failed"
    exit 1
}

echo "✅ Docker image built successfully"

# Test with GPU (if available)
echo ""
echo "🧪 Testing with GPU support..."
echo "Running: docker run --gpus all -p 8080:8080 -v \$(pwd)/test_input.json:/test_input.json transcript-runpod-test"

if docker run --gpus all --rm -v "$(pwd)/test_input.json:/test_input.json" transcript-runpod-test python3 rp_handler.py --test_input /test_input.json; then
    echo "✅ GPU test successful!"
else
    echo "❌ GPU test failed - checking if it's a cuDNN issue..."
    
    # Test CPU fallback
    echo ""
    echo "🔄 Testing CPU fallback..."
    if docker run --rm -v "$(pwd)/test_input.json:/test_input.json" transcript-runpod-test python3 -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
from faster_whisper import WhisperModel
model = WhisperModel('tiny', device='cpu', compute_type='int8')
print('CPU model works!')
"; then
        echo "✅ CPU fallback works - issue is GPU/cuDNN specific"
    else
        echo "❌ Even CPU test failed - fundamental issue"
    fi
fi

echo ""
echo "🚀 To test interactively:"
echo "docker run --gpus all -it --rm transcript-runpod-test bash"
echo ""
echo "📝 To test the local server:"
echo "docker run --gpus all -p 8080:8080 --rm transcript-runpod-test python3 rp_handler.py --rp_serve_api --rp_api_port 8080"
echo "Then: curl -X POST http://localhost:8080/run -H 'Content-Type: application/json' -d @test_input.json"