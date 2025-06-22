FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Create frontend directory and copy Streamlit app
RUN mkdir -p /app/frontend
COPY frontend/streamlit_app.py /app/frontend/

# Make sure the app directory has proper permissions
RUN chmod -R 755 /app

# Create nsf_graphrag_knowledge directory
RUN mkdir -p /app/nsf_graphrag_knowledge

# Expose ports for both services
EXPOSE 8000 8501

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]