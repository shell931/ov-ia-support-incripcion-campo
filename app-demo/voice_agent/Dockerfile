# Voice agent. Build context: app-demo/ (see docker-compose.yml).
FROM python:3.12-slim
WORKDIR /app
COPY voice_agent/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY voice_agent ./voice_agent
# Bake the VAD model into the image so the first call doesn't download it.
RUN python -m voice_agent.main download-files
# Outbound connection to LiveKit (cloud or on-prem): no inbound ports needed.
CMD ["python", "-m", "voice_agent.main", "start"]
