FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for PyMuPDF/fitz
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p data sessions keys uploads

# Copy the rest of the application
COPY . .

# Make sure files exist
RUN touch data/questions.csv

# Environment variable for the port (Cloud Run will set this automatically)
ENV PORT=8080

# Command to run the application
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1 