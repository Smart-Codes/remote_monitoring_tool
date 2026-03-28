# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Create necessary directories
RUN mkdir -p server logs

# Create default users.json if not exists
RUN if [ ! -f server/users.json ]; then \
    echo '{"admin":"8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918","user":"5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"}' > server/users.json; \
    fi

# Expose port
EXPOSE 5000

# Run the server with unbuffered output for better logging
CMD ["python", "-u", "server.py"]