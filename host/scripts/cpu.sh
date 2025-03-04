#!/bin/bash
# Se o arquivo de controle existir, retorna carga alta (95%)
if [ -f "/tmp/simulate_cpu_high" ]; then
    echo "95.0"
    # Gera carga real para mostrar no monitoramento
    stress-ng --cpu 1 --cpu-load 95 --timeout 60 > /dev/null 2>&1 &
else
    # Carga normal entre 10-30%
    echo $(( (RANDOM % 20) + 10 )).$(( RANDOM % 10 ))
fi