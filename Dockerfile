# Use a slim Python base image
FROM python:3.13.0-slim

# Set metadata
LABEL maintainer="Tiger <nxfs.xyz@gmail.com>"
LABEL version="1.0"
LABEL description="Django REST API"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install MySQL dependencies and clean up
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libmariadb-dev \
    pkg-config \
    wakeonlan \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Install curl for healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create docker group and non-root user
RUN groupadd -g 999 docker && \
    useradd -m -u 1000 -G docker tiger && \
    mkdir -p /app && \
    chown tiger:tiger /app

# Set working directory
WORKDIR /app

# Upgrade pip and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

RUN chown -R tiger:tiger /app

# Switch to non-root user
USER tiger

# Expose port (use 8555 if needed, based on your earlier question)
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/ || exit 1

# Run Gunicorn
CMD ["gunicorn", "srv.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2"]