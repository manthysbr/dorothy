#!/bin/bash
# Ativa ou desativa simulação de problemas

usage() {
    echo "Uso: $0 [cpu|disk|memory|service] [on|off]"
    echo "   cpu     - Alta utilização de CPU"
    echo "   disk    - Disco quase cheio"
    echo "   memory  - Alto uso de memória"
    echo "   service - Serviço parado"
    echo "   on      - Ativa problema"
    echo "   off     - Desativa problema"
    exit 1
}

if [ $# -ne 2 ]; then
    usage
fi

PROBLEM=$1
STATE=$2

case "$PROBLEM" in
    cpu)
        FILE="/tmp/simulate_cpu_high"
        ;;
    disk)
        FILE="/tmp/simulate_disk_full"
        ;;
    memory)
        FILE="/tmp/simulate_memory_high"
        ;;
    service)
        FILE="/tmp/simulate_service_down"
        ;;
    *)
        usage
        ;;
esac

case "$STATE" in
    on)
        touch "$FILE"
        echo "Problema $PROBLEM ativado"
        ;;
    off)
        rm -f "$FILE"
        echo "Problema $PROBLEM desativado"
        ;;
    *)
        usage
        ;;
esac