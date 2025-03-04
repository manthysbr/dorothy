#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Construindo a imagem da API Dorothy ===${NC}"
docker build -t dorothy-api .

echo -e "${BLUE}=== Iniciando a API Dorothy ===${NC}"
echo -e "${YELLOW}A API estará disponível em: http://localhost:8000${NC}"

# Inicia o contêiner com variáveis de ambiente para teste
docker run -it --rm \
  -p 8000:8000 \
  -e LOG_LEVEL=debug \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e OLLAMA_MODEL=deepseek-r1:14b \
  --add-host=host.docker.internal:host-gateway \
  --name dorothy-api \
  dorothy-api

# Nota: host.docker.internal permite que o contêiner acesse 
# serviços rodando na máquina host, como o Ollama no WSL