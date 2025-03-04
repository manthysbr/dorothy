FROM python:3.11-slim as builder

# Evita avisos de Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Instala dependências de compilação
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Cria diretório de trabalho
WORKDIR /app

# Copia e instala as dependências separadamente para aproveitar o cache
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Segunda etapa para a imagem final
FROM python:3.11-slim

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Cria diretório para logs
RUN mkdir -p /app/logs && \
    # Cria usuário não-root
    addgroup --system dorothy && \
    adduser --system --ingroup dorothy dorothy && \
    chown -R dorothy:dorothy /app/logs

# Cria e define diretório de trabalho
WORKDIR /app

# Copia as rodas Python da etapa de compilação
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* && \
    rm -rf /wheels

# Copia o código fonte
COPY --chown=dorothy:dorothy . .

# Muda para usuário não-root
USER dorothy

# Porta da aplicação
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Comando de inicialização
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]