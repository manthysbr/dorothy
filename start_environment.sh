#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Iniciando ambiente Dorothy + Zabbix + Ollama ===${NC}"
echo

# Verificar se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker não encontrado! Por favor, instale o Docker e tente novamente.${NC}"
    exit 1
fi

# Verificar se o Docker Compose está instalado
if ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose não encontrado! Por favor, instale o Docker Compose e tente novamente.${NC}"
    exit 1
fi

# Criar diretório para logs se não existir
mkdir -p logs

# Construir imagem da API Dorothy
echo -e "${YELLOW}Construindo imagem da API Dorothy...${NC}"
docker build -t dorothy-api -f docker/dorothy/Dockerfile .

# Iniciar contêineres
echo -e "${YELLOW}Iniciando contêineres...${NC}"
docker compose -f docker/docker-compose.yaml up -d

# Verificar status dos contêineres
echo -e "${YELLOW}Verificando status dos contêineres...${NC}"
sleep 5
docker compose -f docker/docker-compose.yaml ps

# Aguardar o serviço Ollama baixar o modelo
echo -e "${YELLOW}Aguardando o Ollama baixar o modelo llama3...${NC}"
echo "Isso pode levar alguns minutos na primeira execução."
until docker logs ollama 2>&1 | grep -q "llama3.*downloaded"; do
    echo "Aguardando download do modelo..."
    sleep 10
done
echo -e "${GREEN}Modelo llama3 baixado e pronto!${NC}"

# Instalar pacotes para o script de configuração do Zabbix
echo -e "${YELLOW}Instalando dependências para configuração do Zabbix...${NC}"
pip install pyzabbix requests

# Executar script de configuração do Zabbix
echo -e "${YELLOW}Configurando integração do Zabbix com Dorothy API...${NC}"
echo "Aguardando o Zabbix ficar online (pode levar alguns minutos)..."
python3 scripts/setup_zabbix_media_type.py

echo
echo -e "${GREEN}=== Ambiente iniciado com sucesso! ===${NC}"
echo
echo -e "Acesse a interface web do Zabbix: ${YELLOW}http://localhost:8080${NC}"
echo "  - Usuário padrão: Admin"
echo "  - Senha padrão: zabbix"
echo
echo -e "API Dorothy está disponível em: ${YELLOW}http://localhost:8000${NC}"
echo "  - Documentação: http://localhost:8000/docs"
echo
echo -e "Para testar a integração, envie um alerta de teste do Zabbix."
echo -e "Ou use o script de teste: ${YELLOW}python3 tests/debug.py${NC}"