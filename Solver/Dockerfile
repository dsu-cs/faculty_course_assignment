FROM python:3.12-slim

LABEL description="Faculty Course Assignment Flask + Solver service"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000

WORKDIR /app

# Install Python dependencies first for better layer caching.
COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn

# Copy only the application code needed by the Flask service and solver.
COPY Solver ./Solver
COPY solver_server ./solver_server

# Optional default input files remain available inside the container.
RUN mkdir -p /app/output

EXPOSE 5000

# Flask app already exists here:
# solver_server/communications/server.py -> app = Flask(__name__)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--threads", "4", \
     "--timeout", "120", \
     "solver_server.communications.server:app"]
