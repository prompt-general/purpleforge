FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Stratus Red Team CLI
RUN curl -sSL https://github.com/DataDog/stratus-red-team/releases/download/v2.17.0/stratus-red-team_2.17.0_linux_amd64.tar.gz | tar -xz -C /usr/local/bin stratus

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Ensure entrypoint is executable
RUN chmod +x scripts/docker-entrypoint.sh

# Default entrypoint wrapper
ENTRYPOINT ["scripts/docker-entrypoint.sh"]

# Default command (overwritten in docker-compose for workers)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
