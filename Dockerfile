FROM python:3.11-slim

WORKDIR /code

# System deps needed by some wheels (chromadb / sentence-transformers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Persist uploaded-document vectors outside the container layer if desired:
#   docker run -v rag-data:/code/data ...
VOLUME ["/code/data"]
EXPOSE 8000

# The embedding model (~90 MB) is downloaded on first start.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
