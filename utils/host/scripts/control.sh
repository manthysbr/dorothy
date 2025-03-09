#!/bin/bash
# Script para controlar simulações de problemas

COMMAND=$1
PROBLEM=$2

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

LOG_FILE="/var/log/dorothy/simulation.log"

mkdir -p /var/log/dorothy
touch $LOG_FILE

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

case $PROBLEM in
    disk)
        if [ "$COMMAND" = "on" ]; then
            log_message "${RED}Ativando simulação de disco cheio${NC}"
            mkdir -p /tmp/simulate
            dd if=/dev/zero of=/tmp/simulate/big_file bs=1M count=500 2>/dev/null
            echo "DISK_FULL=true" > /tmp/simulate/status
            log_message "Arquivo grande criado em /tmp/simulate/big_file"
        elif [ "$COMMAND" = "off" ]; then
            log_message "${GREEN}Desativando simulação de disco cheio${NC}"
            rm -f /tmp/simulate/big_file
            echo "DISK_FULL=false" > /tmp/simulate/status
            log_message "Arquivo grande removido"
        fi
        ;;
    cpu)
        if [ "$COMMAND" = "on" ]; then
            log_message "${RED}Ativando simulação de alta CPU${NC}"
            stress-ng --cpu 1 --timeout 0 --cpu-method matrixprod &
            echo $! > /tmp/simulate/cpu_pid
            echo "CPU_HIGH=true" >> /tmp/simulate/status
            log_message "Processo de CPU alta iniciado com PID $(cat /tmp/simulate/cpu_pid)"
        elif [ "$COMMAND" = "off" ]; then
            log_message "${GREEN}Desativando simulação de alta CPU${NC}"
            if [ -f /tmp/simulate/cpu_pid ]; then
                kill $(cat /tmp/simulate/cpu_pid) 2>/dev/null || true
                rm -f /tmp/simulate/cpu_pid
                echo "CPU_HIGH=false" >> /tmp/simulate/status
                log_message "Processo de CPU alta finalizado"
            fi
        fi
        ;;
    service)
        if [ "$COMMAND" = "on" ]; then
            log_message "${RED}Ativando simulação de serviço parado${NC}"
            # Simular serviço criando arquivo dummy
            touch /tmp/simulate/dummy_service.pid
            echo "SERVICE_DOWN=true" >> /tmp/simulate/status
            log_message "Serviço dummy marcado como parado"
        elif [ "$COMMAND" = "off" ]; then
            log_message "${GREEN}Desativando simulação de serviço parado${NC}"
            # "Reiniciar" serviço dummy
            rm -f /tmp/simulate/dummy_service.pid
            echo "SERVICE_DOWN=false" >> /tmp/simulate/status
            log_message "Serviço dummy reiniciado"
        fi
        ;;
    memory)
        if [ "$COMMAND" = "on" ]; then
            log_message "${RED}Ativando simulação de uso alto de memória${NC}"
            stress-ng --vm 1 --vm-bytes 80% --timeout 0 &
            echo $! > /tmp/simulate/memory_pid
            echo "MEMORY_HIGH=true" >> /tmp/simulate/status
            log_message "Processo de uso alto de memória iniciado com PID $(cat /tmp/simulate/memory_pid)"
        elif [ "$COMMAND" = "off" ]; then
            log_message "${GREEN}Desativando simulação de uso alto de memória${NC}"
            if [ -f /tmp/simulate/memory_pid ]; then
                kill $(cat /tmp/simulate/memory_pid) 2>/dev/null || true
                rm -f /tmp/simulate/memory_pid
                echo "MEMORY_HIGH=false" >> /tmp/simulate/status
                log_message "Processo de uso alto de memória finalizado"
            fi
        fi
        ;;
    *)
        echo "Uso: $0 [on|off] [disk|cpu|service|memory]"
        echo "Exemplo: $0 on disk"
        echo "         $0 off cpu"
        exit 1
        ;;
esac

# Mostrar status atual
echo
echo -e "${YELLOW}Status atual das simulações:${NC}"
cat /tmp/simulate/status 2>/dev/null || echo "Nenhuma simulação ativa"