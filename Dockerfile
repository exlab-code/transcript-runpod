FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy handler
COPY rp_handler.py .

# Start the handler
CMD python -u rp_handler.py