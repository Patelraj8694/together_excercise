FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Default command (overridden by docker-compose per service)
CMD ["python", "-m", "budget_pacing.app"]
