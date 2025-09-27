FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.headless", "true", "--server.fileWatcherType=poll"]