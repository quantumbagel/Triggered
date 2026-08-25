FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TRIGGERED_AUTO_UPDATE=false \
    TRIGGERED_CHECK_FOR_UPDATES=false

COPY pyproject.toml README.md ./
COPY bot.py ./
COPY actions ./actions
COPY backend ./backend
COPY configuration/requirements.json configuration/config.example.json ./configuration/
COPY docker/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && pip install --no-cache-dir .

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "bot.py"]
