FROM python:3.11-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Fix numpy compatibility issue
RUN pip uninstall -y numpy && pip install numpy==1.24.3

# Copy the rest of the application code
COPY . .

# Make our startup script executable
RUN chmod +x startup.sh

# Create needed directories
RUN mkdir -p sessions uploads data keys

# Make sure the service account file has proper permissions
RUN chmod 644 *.json || true

# Set environment variables (these can be overridden at runtime)
ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PORT=8080

# Run the application using our startup script
CMD ["./startup.sh"] 