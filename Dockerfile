FROM python:3.9-slim

WORKDIR /app

# Install Wine and other dependencies needed for MetaTrader5
RUN apt-get update && apt-get install -y --no-install-recommends \
    wine \
    wine32 \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set up environment variables
ENV DISPLAY=:0
ENV WINEDEBUG=-all

# Start Xvfb and run the application
CMD Xvfb :0 -screen 0 1024x768x16 & uvicorn app.main:app --host 0.0.0.0 --port 8000