#!/bin/bash
# filepath: /home/gohan/dorothy/scripts/simulate_environment.sh

# Definição de cores para melhor visualização
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Função para exibir banner
show_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║                    DOROTHY PROBLEM SIMULATOR                  ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Função para simular problemas
simulate_problem() {
    local problem_type=$1
    local action=$2
    
    echo -e "${YELLOW}=== Simulando problema: $problem_type ($action) ===${NC}"
    
    docker exec -it zabbix-agent-simulator bash -c "mkdir -p /etc/zabbix/scripts"
    
    case $problem_type in
        disk)
            if [ "$action" == "on" ]; then
                echo "Ativando simulação de disco cheio..."
                docker exec -it zabbix-agent-simulator bash -c "echo '95' > /etc/zabbix/scripts/simulate_disk_full.txt"
            else
                echo "Desativando simulação de disco cheio..."
                docker exec -it zabbix-agent-simulator bash -c "echo '30' > /etc/zabbix/scripts/simulate_disk_full.txt"
            fi
            ;;
        cpu)
            if [ "$action" == "on" ]; then
                echo "Ativando simulação de CPU alta..."
                docker exec -it zabbix-agent-simulator bash -c "echo '95' > /etc/zabbix/scripts/simulate_cpu_high.txt"
            else
                echo "Desativando simulação de CPU alta..."
                docker exec -it zabbix-agent-simulator bash -c "echo '10' > /etc/zabbix/scripts/simulate_cpu_high.txt"
            fi
            ;;
        memory)
            if [ "$action" == "on" ]; then
                echo "Ativando simulação de memória alta..."
                docker exec -it zabbix-agent-simulator bash -c "echo '95' > /etc/zabbix/scripts/simulate_memory_high.txt"
            else
                echo "Desativando simulação de memória alta..."
                docker exec -it zabbix-agent-simulator bash -c "echo '30' > /etc/zabbix/scripts/simulate_memory_high.txt"
            fi
            ;;
        service)
            if [ "$action" == "on" ]; then
                echo "Ativando simulação de serviço parado..."
                docker exec -it zabbix-agent-simulator bash -c "echo '0' > /etc/zabbix/scripts/simulate_service_down.txt"
            else
                echo "Desativando simulação de serviço parado..."
                docker exec -it zabbix-agent-simulator bash -c "echo '1' > /etc/zabbix/scripts/simulate_service_down.txt"
            fi
            ;;
        *)
            echo -e "${RED}Tipo de problema inválido. Use: disk, cpu, memory, service${NC}"
            return 1
            ;;
    esac
    
    echo -e "${GREEN}Simulação configurada com sucesso!${NC}"
    
    # Verificar arquivos criados
    echo -e "${YELLOW}Arquivos de simulação:${NC}"
    docker exec -it zabbix-agent-simulator bash -c "ls -la /etc/zabbix/scripts/simulate_*.txt 2>/dev/null || echo 'Nenhum arquivo encontrado'"
    docker exec -it zabbix-agent-simulator bash -c "cat /etc/zabbix/scripts/simulate_${problem_type}*.txt 2>/dev/null || echo 'Arquivo não encontrado'"
}

# Função para ver o status atual dos contêineres
check_status() {
    echo -e "${YELLOW}=== Verificando Status do Ambiente ===${NC}"
    
    echo -e "${BLUE}Contêineres ativos:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E 'zabbix|dorothy|rundeck|ollama'
    
    echo -e "\n${BLUE}Status do simulador:${NC}"
    docker exec -it zabbix-agent-simulator bash -c "ls -la /etc/zabbix/scripts/simulate_*.txt 2>/dev/null || echo 'Nenhum problema simulado ativo'"
    docker exec -it zabbix-agent-simulator bash -c "cat /etc/zabbix/scripts/simulate_*.txt 2>/dev/null || echo ''"
    
    echo -e "\n${BLUE}Problemas no Zabbix:${NC}"
    echo "Acesse: http://localhost:8080 → Monitoramento → Problemas"
    
    echo -e "\n${BLUE}Logs da API:${NC}"
    docker logs --tail 10 dorothy-api | grep -E "INFO|ERROR|WARN|DEBUG" || echo "Nenhum log recente"
}

# Função para testar diretamente a API
test_api_directly() {
    local problem_type=$1
    
    echo -e "${YELLOW}=== Testando API Diretamente ===${NC}"
    
    case $problem_type in
        disk)
            payload='{
                "event_id": "test-12345",
                "host": "Problem-Simulator",
                "problem": "Espaço em disco crítico: 95% utilizado em /var",
                "severity": "high",
                "status": "PROBLEM",
                "timestamp": '"$(date +%s)"',
                "details": {
                    "ip": "172.19.0.9",
                    "description": "Disco cheio no servidor",
                    "item_value": "95%",
                    "filesystem": "/var"
                },
                "tags": [
                    {"tag": "component", "value": "disk"},
                    {"tag": "environment", "value": "production"}
                ]
            }'
            ;;
        cpu)
            payload='{
                "event_id": "test-12346",
                "host": "Problem-Simulator",
                "problem": "Alta utilização de CPU: 95% por mais de 15 minutos",
                "severity": "high",
                "status": "PROBLEM",
                "timestamp": '"$(date +%s)"',
                "details": {
                    "ip": "172.19.0.9",
                    "description": "CPU alta no servidor",
                    "item_value": "95%",
                    "duration": "15 minutes"
                },
                "tags": [
                    {"tag": "component", "value": "cpu"},
                    {"tag": "environment", "value": "production"}
                ]
            }'
            ;;
        memory)
            payload='{
                "event_id": "test-12347",
                "host": "Problem-Simulator",
                "problem": "Alta utilização de memória: 95% por mais de 10 minutos",
                "severity": "high",
                "status": "PROBLEM",
                "timestamp": '"$(date +%s)"',
                "details": {
                    "ip": "172.19.0.9",
                    "description": "Memória alta no servidor",
                    "item_value": "95%",
                    "duration": "10 minutes"
                },
                "tags": [
                    {"tag": "component", "value": "memory"},
                    {"tag": "environment", "value": "production"}
                ]
            }'
            ;;
        service)
            payload='{
                "event_id": "test-12348",
                "host": "Problem-Simulator",
                "problem": "Serviço apache2 parado",
                "severity": "high",
                "status": "PROBLEM",
                "timestamp": '"$(date +%s)"',
                "details": {
                    "ip": "172.19.0.9",
                    "description": "Serviço web parado",
                    "service_name": "apache2",
                    "item_value": "stopped"
                },
                "tags": [
                    {"tag": "component", "value": "service"},
                    {"tag": "service", "value": "web"}
                ]
            }'
            ;;
        *)
            echo -e "${RED}Tipo de problema inválido. Use: disk, cpu, memory, service${NC}"
            return 1
            ;;
    esac
    
    echo -e "${BLUE}Enviando payload para a API:${NC}"
    echo "$payload" | jq '.' || echo "$payload"
    
    echo -e "\n${BLUE}Resposta da API:${NC}"
    curl -s -X POST \
      -H "Content-Type: application/json" \
      -d "$payload" \
      http://localhost:8000/api/v1/zabbix/alert | jq '.' || \
    curl -s -X POST \
      -H "Content-Type: application/json" \
      -d "$payload" \
      http://localhost:8000/api/v1/zabbix/alert
}

# Função para monitorar logs em tempo real
monitor_logs() {
    echo -e "${YELLOW}=== Monitorando Logs em Tempo Real ===${NC}"
    echo -e "${BLUE}Pressione Ctrl+C para sair${NC}"
    
    docker logs -f --tail 20 dorothy-api
}

# Menu principal
show_menu() {
    clear
    show_banner
    echo -e "${PURPLE}Escolha uma opção:${NC}"
    echo "1) Simular problema de disco cheio"
    echo "2) Simular problema de CPU alta"
    echo "3) Simular problema de memória alta"
    echo "4) Simular problema de serviço parado"
    echo "5) Desativar todas as simulações"
    echo "6) Verificar status do ambiente"
    echo "7) Testar API diretamente (sem Zabbix)"
    echo "8) Monitorar logs da API em tempo real"
    echo "0) Sair"
    echo -n "Opção: "
    read -r option
    
    case $option in
        1) simulate_problem disk on; press_enter ;;
        2) simulate_problem cpu on; press_enter ;;
        3) simulate_problem memory on; press_enter ;;
        4) simulate_problem service on; press_enter ;;
        5) 
           simulate_problem disk off
           simulate_problem cpu off
           simulate_problem memory off
           simulate_problem service off
           press_enter
           ;;
        6) check_status; press_enter ;;
        7)
           echo -e "${PURPLE}Escolha o tipo de problema para testar:${NC}"
           echo "1) Disco cheio"
           echo "2) CPU alta"
           echo "3) Memória alta"
           echo "4) Serviço parado"
           echo -n "Tipo: "
           read -r problem_type
           case $problem_type in
               1) test_api_directly disk ;;
               2) test_api_directly cpu ;;
               3) test_api_directly memory ;;
               4) test_api_directly service ;;
               *) echo -e "${RED}Opção inválida!${NC}" ;;
           esac
           press_enter
           ;;
        8) monitor_logs ;;
        0) exit 0 ;;
        *) echo -e "${RED}Opção inválida!${NC}"; press_enter ;;
    esac
}

# Função para "pressione Enter para continuar"
press_enter() {
    echo
    read -rp "Pressione Enter para continuar..."
}

# Verificar pacotes necessários
check_dependencies() {
    which jq >/dev/null 2>&1 || {
        echo -e "${YELLOW}O pacote 'jq' não está instalado. Tentando instalar...${NC}"
        sudo apt update && sudo apt install -y jq || {
            echo -e "${RED}Não foi possível instalar o pacote 'jq'.${NC}"
            echo "Por favor, instale manualmente: sudo apt install jq"
            exit 1
        }
    }
}

# Verificar se o ambiente está rodando
check_environment() {
    docker ps | grep -q dorothy-api || {
        echo -e "${RED}Ambiente Dorothy não está em execução!${NC}"
        echo "Execute primeiro: ./start_environment.sh"
        exit 1
    }
}

# Execução principal
check_dependencies
check_environment
while true; do
    show_menu
done