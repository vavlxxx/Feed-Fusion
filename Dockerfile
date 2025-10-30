FROM python:3.11.9

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install poetry --no-cache-dir
RUN poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-interaction --no-cache

COPY . .
CMD poetry run alembic upgrade head; \
	poetry run python src/main.py