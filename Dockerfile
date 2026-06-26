FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV AWS_DEFAULT_REGION=eu-west-2

WORKDIR /app

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY cost_guardian.py README.md ./

ENTRYPOINT ["python", "/app/cost_guardian.py"]
