FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml ./
RUN uv pip install --system -r pyproject.toml --extra postgres
COPY app ./app
EXPOSE 8000
CMD ["fastapi", "run", "app/main.py", "--port", "8000"]
