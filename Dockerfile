FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

WORKDIR /

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with proper CUDA support
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler
COPY rp_handler.py .

# Start the handler  
CMD python -u rp_handler.py