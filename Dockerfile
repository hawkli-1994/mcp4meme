FROM python:3.13-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py .

# Expose port for HTTP mode (optional)
EXPOSE 8000

# Default command runs in STDIO mode
CMD ["python", "mcp_server.py"]