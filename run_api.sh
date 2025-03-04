#!/bin/bash

# Certifica-se de que estamos no diretório raiz do projeto
cd "$(dirname "$0")"

echo "Verificando se requirements.txt existe..."
if [ ! -f "requirements.txt" ]; then
    echo "Criando arquivo requirements.txt..."
    cat > requirements.txt << EOF
fastapi
uvicorn
httpx
python-dotenv
pydantic>=2.0.0
pydantic-settings
aiohttp
EOF
fi

echo "Construindo a imagem Docker..."
docker build -t dorothy-api .

echo "Iniciando o contêiner..."
docker run -it --rm \
  -p 8000:8000 \
  -e LOG_LEVEL=debug \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e OLLAMA_MODEL=llama3.2 \
  --add-host=host.docker.internal:host-gateway \
  --name dorothy-api \
  dorothy-api