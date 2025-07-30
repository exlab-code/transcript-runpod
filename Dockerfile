FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /

# Install NVIDIA cuDNN libraries via pip (the key fix!)
RUN pip install nvidia-cublas-cu11 nvidia-cudnn-cu11

# Set LD_LIBRARY_PATH to point to cuDNN libraries
RUN echo 'export LD_LIBRARY_PATH=`python3 -c "import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + \":\" + os.path.dirname(nvidia.cudnn.lib.__file__))"`' >> ~/.bashrc

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler
COPY rp_handler.py .

# Set the LD_LIBRARY_PATH for the container runtime
ENV LD_LIBRARY_PATH=/opt/conda/lib/python3.10/site-packages/nvidia/cublas/lib:/opt/conda/lib/python3.10/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH

# Start the handler
CMD python -u rp_handler.py