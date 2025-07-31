FROM runpod/pytorch:2.2.0-py3.10-cuda12.1.1-devel-ubuntu22.04

WORKDIR /

# The base image already includes CUDA 12.1 and cuDNN - no additional installs needed

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler
COPY rp_handler.py .

# cuDNN and CUDA libraries are already configured in the base image

# Start the handler
CMD python3 -u rp_handler.py