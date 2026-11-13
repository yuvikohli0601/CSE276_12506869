# CivicPulse Dockerfile for Free Cloud & Hugging Face Spaces Deployment
# Course: CSE276 | Problem Statement: SIH25031
# Author: Yuvi Kohli (Reg: 12506869, Roll: RK3P25ILB43, Group: K3P25IL)

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY codebase/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app

# Create non-root user (Standard for Hugging Face Spaces & security best practices)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

ENV PYTHONPATH=/app/codebase
EXPOSE 7860 8000

CMD ["python", "codebase/backend/app.py"]
