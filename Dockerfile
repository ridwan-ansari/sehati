FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true

WORKDIR /app

RUN pip install --no-cache-dir poetry

# install deps in their own layer first so `docker build` skips this step when only app code changes
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-directory

COPY . .
RUN poetry install --only main --no-root

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
