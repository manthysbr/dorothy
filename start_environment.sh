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

# Criar diretórios para scripts do simulador se não existirem
mkdir -p docker/zabbix-agent-simulator/scripts

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

# Aguardar o serviço Ollama iniciar
echo -e "${YELLOW}Aguardando o serviço Ollama iniciar...${NC}"
echo "Isso pode levar alguns segundos."
max_retries=20
retry_count=0
while ! docker exec -i ollama ollama list >/dev/null 2>&1; do
    echo "Aguardando o Ollama iniciar... ($((retry_count+1))/$max_retries)"
    sleep 5
    retry_count=$((retry_count+1))
    if [ $retry_count -ge $max_retries ]; then
        echo -e "${RED}Tempo limite excedido aguardando o Ollama iniciar.${NC}"
        break
    fi
done

# Baixar o modelo llama3.2
echo -e "${YELLOW}Baixando o modelo llama3.2...${NC}"
echo "Isso pode levar alguns minutos na primeira execução."
docker exec -i ollama ollama pull llama3.2

# Configurar host simulador no Zabbix
echo -e "${YELLOW}Configurando host simulador no Zabbix...${NC}"
echo "Aguardando o Zabbix ficar online (pode levar alguns minutos)..."
max_retries=30
retry_count=0
while ! curl -s http://localhost:8080 | grep -q Zabbix; do
    echo "Aguardando o Zabbix Web ficar disponível... ($((retry_count+1))/$max_retries)"
    sleep 10
    retry_count=$((retry_count+1))
    if [ $retry_count -ge $max_retries ]; then
        echo -e "${RED}Tempo limite excedido aguardando o Zabbix iniciar.${NC}"
        break
    fi
done

# Instalar pacotes para o script de configuração do Zabbix
echo -e "${YELLOW}Instalando dependências para configuração do Zabbix...${NC}"
pip install pyzabbix requests

# Executar script de configuração do Zabbix
echo -e "${YELLOW}Configurando integração do Zabbix com Dorothy API...${NC}"
if [ -f "scripts/setup_zabbix_media_type.py" ]; then
    python3 scripts/setup_zabbix_media_type.py
else
    echo -e "${RED}Script de configuração do Zabbix não encontrado.${NC}"
    echo "Copie o script para scripts/setup_zabbix_media_type.py"
fi

echo -e "${YELLOW}Adicionando host simulador ao Zabbix...${NC}"
if [ -f "scripts/add_simulator_host.py" ]; then
    python3 scripts/add_simulator_host.py
else
    echo -e "${RED}Script de adição de host não encontrado.${NC}"
    echo "Copie o script para scripts/add_simulator_host.py"
fi

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