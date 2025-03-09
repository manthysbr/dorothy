#!/bin/bash
# Arquivo: host/scripts/simulate_problem.sh

SIMULATE_DIR="/etc/zabbix/scripts"
mkdir -p $SIMULATE_DIR

function usage() {
  echo "Uso: $0 [tipo_problema] [on|off]"
  echo "Tipos de problema: disk, cpu, memory, service"
  echo "Exemplo: $0 disk on"
}

if [ $# -lt 2 ]; then
  usage
  exit 1
fi

PROBLEM=$1
ACTION=$2

case $PROBLEM in
  disk)
    if [ "$ACTION" == "on" ]; then
      echo "95" > $SIMULATE_DIR/simulate_disk_full.txt
      echo "Problema de disco simulado ATIVADO"
    else
      echo "30" > $SIMULATE_DIR/simulate_disk_full.txt
      echo "Problema de disco simulado DESATIVADO"
    fi
    ;;
    
  cpu)
    if [ "$ACTION" == "on" ]; then
      echo "95" > $SIMULATE_DIR/simulate_cpu_high.txt
      echo "Problema de CPU simulado ATIVADO"
    else
      echo "10" > $SIMULATE_DIR/simulate_cpu_high.txt
      echo "Problema de CPU simulado DESATIVADO"
    fi
    ;;
    
  memory)
    if [ "$ACTION" == "on" ]; then
      echo "95" > $SIMULATE_DIR/simulate_memory_high.txt
      echo "Problema de memória simulado ATIVADO"
    else
      echo "30" > $SIMULATE_DIR/simulate_memory_high.txt
      echo "Problema de memória simulado DESATIVADO"
    fi
    ;;
    
  service)
    if [ "$ACTION" == "on" ]; then
      echo "0" > $SIMULATE_DIR/simulate_service_down.txt
      echo "Problema de serviço simulado ATIVADO"
    else
      echo "1" > $SIMULATE_DIR/simulate_service_down.txt
      echo "Problema de serviço simulado DESATIVADO"
    fi
    ;;
    
  *)
    usage
    exit 1
    ;;
esac