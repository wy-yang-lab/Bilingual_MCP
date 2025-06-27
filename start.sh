#!/bin/bash

# Render startup script for MCP Bilingual Terminology Checker

# Set environment variables if not set
export PYTHONPATH="${PYTHONPATH}:/app"

# Start the FastAPI server
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} 