FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for libraries or PostgreSQL drivers
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/nickbabcock/rrrocket/releases/download/v0.11.5/rrrocket-0.11.5-x86_64-unknown-linux-musl.tar.gz \
    && tar -xzf rrrocket-0.11.5-x86_64-unknown-linux-musl.tar.gz \
    && mv rrrocket /usr/local/bin/rrrocket \
    && chmod +x /usr/local/bin/rrrocket \
    && rm rrrocket-0.11.5-x86_64-unknown-linux-musl.tar.gz


# Copy dependencies list
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend files
COPY . .

# Start FastAPI using uvicorn
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]