#!/bin/bash
# filepath: /home/gohan/dorothy/scripts/test_connectivity.sh

# Definição de cores para melhor visualização
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Teste de Conectividade entre Contêineres Dorothy ===${NC}"

# Função para obter informações de rede dos contêineres
get_container_network_info() {
    echo -e "\n${YELLOW}=== Informações de Rede dos Contêineres ===${NC}"
    
    printf "%-25s %-15s %-20s\n" "CONTÊINER" "IP" "REDE"
    printf "%-25s %-15s %-20s\n" "----------" "---" "----"
    
    for container in $(docker ps --format "{{.Names}}"); do
        ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $container)
        network=$(docker inspect -f '{{range $net, $conf := .NetworkSettings.Networks}}{{$net}} {{end}}' $container)
        printf "%-25s %-15s %-20s\n" "$container" "$ip" "$network"
    done
}

# Função para testar conectividade básica (ping)
test_ping_connectivity() {
    echo -e "\n${YELLOW}=== Teste de Conectividade por Ping ===${NC}"
    
    local source_containers=("zabbix-server" "dorothy-api" "rundeck" "zabbix-agent-simulator")
    local target_containers=("zabbix-server" "dorothy-api" "rundeck" "zabbix-agent-simulator" "ollama")
    
    printf "%-20s %-20s %-10s\n" "ORIGEM" "DESTINO" "STATUS"
    printf "%-20s %-20s %-10s\n" "------" "-------" "------"
    
    for src in "${source_containers[@]}"; do
        for dest in "${target_containers[@]}"; do
            if [ "$src" != "$dest" ]; then
                echo -n "Testando $src -> $dest: "
                if docker exec $src ping -c 1 -W 2 $dest > /dev/null 2>&1; then
                    printf "%-20s %-20s ${GREEN}%-10s${NC}\n" "$src" "$dest" "✓ OK"
                else
                    printf "%-20s %-20s ${RED}%-10s${NC}\n" "$src" "$dest" "✗ FALHA"
                fi
            fi
        done
    done
}

# Função para testar endpoints HTTP
test_http_endpoints() {
    echo -e "\n${YELLOW}=== Teste de Endpoints HTTP ===${NC}"
    
    local endpoints=(
        "dorothy-api:8000/docs API-Docs"
        "zabbix-web:8080 Zabbix-Web"
        "rundeck:4440 Rundeck"
        "ollama:11434/api/version Ollama-API"
    )
    
    local requesters=("zabbix-server" "dorothy-api" "rundeck")
    
    printf "%-15s %-25s %-10s\n" "ORIGEM" "DESTINO" "STATUS"
    printf "%-15s %-25s %-10s\n" "------" "-------" "------"
    
    for requester in "${requesters[@]}"; do
        for endpoint_info in "${endpoints[@]}"; do
            endpoint=$(echo $endpoint_info | cut -d' ' -f1)
            service=$(echo $endpoint_info | cut -d' ' -f2)
            
            # Extrair host e caminho
            host=$(echo $endpoint | cut -d: -f1)
            port=$(echo $endpoint | cut -d: -f2 | cut -d/ -f1)
            path=$(echo $endpoint | grep -o '/.*$' || echo "/")
            
            echo -n "Testando $requester -> $service: "
            
            status=$(docker exec -it $requester curl -s -o /dev/null -w "%{http_code}" -m 5 http://$host:$port$path)
            
            if [[ "$status" == "000" ]]; then
                printf "%-15s %-25s ${RED}%-10s${NC}\n" "$requester" "$service" "✗ FALHA"
            elif [[ "$status" =~ ^[2-3] ]]; then
                printf "%-15s %-25s ${GREEN}%-10s${NC}\n" "$requester" "$service" "✓ OK ($status)"
            else
                printf "%-15s %-25s ${YELLOW}%-10s${NC}\n" "$requester" "$service" "⚠ $status"
            fi
        done
    done
}

# Função para testar específicamente a comunicação Zabbix webhook -> Dorothy API
test_webhook_connectivity() {
    echo -e "\n${YELLOW}=== Teste de Comunicação Webhook Zabbix -> Dorothy API ===${NC}"
    
    local test_payload='{
        "event_id": "test-123456",
        "host": "test-host",
        "problem": "Test alert - please ignore",
        "severity": "information",
        "status": "PROBLEM",
        "timestamp": '$(date +%s)',
        "details": {
            "description": "Teste de conectividade webhook"
        }
    }'
    
    echo -e "Enviando webhook de teste do Zabbix para Dorothy API..."
    
    local response=$(docker exec -it zabbix-server curl -s -w "\nSTATUS:%{http_code}" \
                     -H "Content-Type: application/json" \
                     -d "$test_payload" \
                     http://dorothy-api:8000/api/v1/zabbix/alert)
    
    local status_code=$(echo "$response" | grep STATUS: | cut -d: -f2)
    local body=$(echo "$response" | grep -v STATUS:)
    
    echo -e "Status HTTP: $status_code"
    echo -e "Resposta: $body"
    
    if [[ "$status_code" =~ ^[2] ]]; then
        echo -e "${GREEN}✓ Webhook entregue com sucesso!${NC}"
    else
        echo -e "${RED}✗ Falha na entrega do webhook!${NC}"
        echo -e "\n${YELLOW}Verificando endpoints disponíveis na API:${NC}"
        docker exec -it dorothy-api curl -s http://localhost:8000/docs | grep -o 'path":"[^"]*' || echo "Nenhuma documentação encontrada"
    fi
}

# Execução principal
get_container_network_info
test_ping_connectivity
test_http_endpoints
test_webhook_connectivity

echo -e "\n${BLUE}=== Teste de Conectividade Concluído ===${NC}"