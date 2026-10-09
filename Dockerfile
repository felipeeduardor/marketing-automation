FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
# Downloads can be slow on first local Docker builds. Keep retries/timeouts explicit
# so a temporary PyPI delay does not abort the development environment setup.
RUN pip install --no-cache-dir --retries 5 --timeout 120 -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
