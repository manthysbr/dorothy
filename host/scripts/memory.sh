#!/bin/bash
# Se o arquivo de controle existir, retorna uso alto de memória (90%)
if [ -f "/tmp/simulate_memory_high" ]; then
    echo "90.0"
    # Consome memória real para mostrar no monitoramento
    stress-ng --vm 1 --vm-bytes 80% --timeout 60 > /dev/null 2>&1 &
else
    # Uso normal de memória (entre 30-50%)
    echo $(( (RANDOM % 20) + 30 )).$(( RANDOM % 10 ))
fi