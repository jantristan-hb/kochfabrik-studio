FROM python:3.12-slim

# Engine-Runtime: node (reconstruct.js) + LibreOffice headless
# (pptx→pdf) + poppler-utils (pdftotext/pdfinfo/pdftoppm — PDF-Input
# des Präsentationsgenerators) + Schriften für faithful Render.
RUN apt-get update && apt-get install -y --no-install-recommends \
      nodejs libreoffice-impress libreoffice-core poppler-utils \
      fonts-dejavu-core fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY web ./web
COPY engine ./engine
# Alembic-Config: backend/migrate.py ruft `alembic -c alembic.ini` (cwd /app);
# fehlt sie, scheitert die Migration mit rc≠0 (F-S-01).
COPY alembic.ini .

ENV KF_IMG_MODEL=gemini-3-pro-image-preview
EXPOSE 8000
# Schema-Migration (idempotent, graceful — nie fatal) vor dem Server.
CMD ["sh","-c","python -m backend.migrate; exec uvicorn backend.app:app --host 0.0.0.0 --port 8000"]
