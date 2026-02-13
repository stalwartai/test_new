# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (needed for Spacy and other libs)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install PyTorch CPU version FIRST (to avoid downloading 2GB+ NVIDIA drivers)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Spacy model
RUN python -m spacy download en_core_web_sm

# "Bake" the SentenceTransformer model into the image
# This prevents downloading it at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Copy the start script and make it executable
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run the start script
CMD ["./start.sh"]
