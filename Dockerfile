# Use slim Python 3.11 base
FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LD_LIBRARY_PATH=/app

# Install 32-bit libraries required by amxxpc
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        libc6:i386 \
        libstdc++6:i386 \
        git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure compiler executable
RUN chmod +x /app/amxxpc

# Expose port (Koyeb uses port 8000 by default)
EXPOSE 8000

# Run Flask app with Gunicorn
# Use 1 worker for free tier, increase for paid plans
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "120", "server:app"]
