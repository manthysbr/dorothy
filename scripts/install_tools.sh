#!/bin/bash
# filepath: /home/gohan/dorothy/scripts/install_diagnostic_tools.sh

echo "=== Instalando ferramentas de diagnóstico nos contêineres ==="

# Função para instalar pacotes em um contêiner
install_tools() {
    local container=$1
    echo "📦 Instalando ferramentas no contêiner $container..."
    
    # Verificar se o contêiner está rodando
    if ! docker ps | grep -q $container; then
        echo "❌ Contêiner $container não está rodando. Pulando."
        return
    fi
    
    # Verificar se já tem curl instalado
    if docker exec -it $container which curl >/dev/null 2>&1; then
        echo "✅ curl já está instalado no contêiner $container."
    else
        echo "🔄 Instalando curl e ferramentas de rede no contêiner $container..."
        docker exec -it -u 0 $container bash -c "apt-get update && apt-get install -y curl iputils-ping net-tools dnsutils" || \
        docker exec -it -u 0 $container bash -c "apk update && apk add curl iputils busybox-extras bind-tools"
    fi
}

# Lista de contêineres para instalar as ferramentas
containers=("zabbix-server" "dorothy-api" "zabbix-web" "rundeck" "zabbix-agent-simulator" "ollama")

# Instalar ferramentas em cada contêiner
for container in "${containers[@]}"; do
    install_tools $container
done

echo "=== Instalação de ferramentas concluída ==="