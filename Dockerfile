FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

COPY cost_guardian.py README.md ./

RUN mkdir -p /app/reports

ENTRYPOINT ["python", "/app/cost_guardian.py"]
CMD ["--format", "markdown"]
