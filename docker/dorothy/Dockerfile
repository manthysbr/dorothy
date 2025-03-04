FROM python:3.11-slim

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Primeiro copiamos apenas os requirements para aproveitar o cache do Docker
COPY requirements.txt .

# Instalamos as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Agora copiamos o resto do código
COPY . .

# Criamos diretório para logs
RUN mkdir -p logs

# Porta da aplicação
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]