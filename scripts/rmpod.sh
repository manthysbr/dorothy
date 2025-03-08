#!/bin/bash
# Script para reconstruir o contêiner dorothy-api com as correções

# Cores para output
VERDE='\033[0;32m'
AMARELO='\033[1;33m'
SEM_COR='\033[0m'

echo -e "${AMARELO}=== Reconstruindo a imagem dorothy-api ===${SEM_COR}"

# 1. Navegar para o diretório raiz do projeto
cd /home/gohan/dorothy

# 2. Construir a nova imagem
echo "Construindo nova imagem..."
docker build -t dorothy-api:latest -f docker/dorothy/Dockerfile .

# 3. Parar o contêiner existente
echo "Parando contêiner existente..."
docker stop dorothy-api

# 4. Remover o contêiner existente
echo "Removendo contêiner..."
docker rm dorothy-api

# 5. Iniciar novo contêiner com a imagem atualizada
echo "Iniciando novo contêiner..."
docker run -d \
    --name dorothy-api \
    --network dorothy-network \
    -e OLLAMA_BASE_URL=http://ollama:11434 \
    -e OLLAMA_MODEL=llama3.2 \
    -e RUNDECK_API_URL=http://rundeck:4440/api/41 \
    -e RUNDECK_TOKEN=admin12345 \
    -e LOG_LEVEL=debug \
    -p 8000:8000 \
    dorothy-api:latest

echo -e "${VERDE}Contêiner reconstruído e iniciado com sucesso!${SEM_COR}"
echo "Verificando logs para confirmar funcionamento..."
sleep 2
docker logs dorothy-api | tail -20