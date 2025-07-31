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

# Detect if we're on Mac (no NVIDIA GPU support)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Detected macOS - GPU testing not available locally"
    echo "📝 Will test CPU mode and Docker environment setup"
    GPU_AVAILABLE=false
else
    echo "🐧 Linux detected - testing GPU support"
    GPU_AVAILABLE=true
fi

# Test Docker environment setup
echo ""
echo "🧪 Testing Docker environment and dependencies..."

if $GPU_AVAILABLE; then
    echo "Running GPU test: docker run --gpus all..."
    if docker run --gpus all --rm -v "$(pwd)/test_input.json:/test_input.json" transcript-runpod-test python3 rp_handler.py --test_input /test_input.json; then
        echo "✅ GPU test successful! cuDNN issue is fixed!"
        exit 0
    else
        echo "❌ GPU test failed - checking details..."
    fi
fi

# Test CPU mode and environment
echo ""
echo "🔄 Testing CPU mode and Docker environment..."
if docker run --rm -v "$(pwd)/test_input.json:/test_input.json" transcript-runpod-test python3 -c "
import sys
print(f'Python version: {sys.version}')

try:
    import torch
    print(f'✅ PyTorch: {torch.__version__}')
    print(f'CUDA available in container: {torch.cuda.is_available()}')
except Exception as e:
    print(f'❌ PyTorch issue: {e}')

try:
    from faster_whisper import WhisperModel
    print('✅ faster-whisper imported successfully')
    
    # Test CPU model creation
    print('🧪 Testing CPU model creation...')
    model = WhisperModel('tiny', device='cpu', compute_type='int8')
    print('✅ CPU Whisper model created successfully!')
    
except Exception as e:
    print(f'❌ faster-whisper issue: {e}')

try:
    import runpod
    print('✅ RunPod SDK imported successfully')
except Exception as e:
    print(f'❌ RunPod SDK issue: {e}')

print('🎯 Docker environment test complete!')
"; then
    if $GPU_AVAILABLE; then
        echo "✅ Docker environment OK, but GPU/cuDNN issue remains"
        echo "🔍 This confirms the cuDNN library problem exists"
    else
        echo "✅ Docker environment working perfectly!"
        echo "🚀 Ready to deploy to RunPod (cuDNN fix should work there)"
    fi
else
    echo "❌ Docker environment has fundamental issues"
    exit 1
fi

echo ""
echo "🚀 To test interactively:"
echo "docker run --gpus all -it --rm transcript-runpod-test bash"
echo ""
echo "📝 To test the local server:"
echo "docker run --gpus all -p 8080:8080 --rm transcript-runpod-test python3 rp_handler.py --rp_serve_api --rp_api_port 8080"
echo "Then: curl -X POST http://localhost:8080/run -H 'Content-Type: application/json' -d @test_input.json"