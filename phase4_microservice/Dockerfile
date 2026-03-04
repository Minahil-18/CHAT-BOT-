FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8000
# When running in Docker, Ollama runs on the host machine.
# host.docker.internal resolves automatically on Docker Desktop (Win/Mac).
# On Linux: docker run --add-host=host.docker.internal:host-gateway ...
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434
ENV MODEL_NAME=qwen2.5:1.5b
ENV PORT=8000
ENV MAX_TOKENS=400
ENV MAX_HISTORY=20

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
