FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md alembic.ini ./
COPY migrations ./migrations
COPY src ./src
RUN python -m pip install --no-cache-dir .
EXPOSE 8000
# Run `alembic upgrade head` as a controlled release/migration step before
# deploying the application. Do not let every replica race to migrate on boot.
CMD ["uvicorn", "myeconomy.main:app", "--host", "0.0.0.0", "--port", "8000"]
