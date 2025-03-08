#!/bin/bash
# Script para limpeza de disco (simulação)

echo "=== INICIANDO LIMPEZA DE DISCO ==="
echo "Data/Hora: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Caminho: ${RD_OPTION_PATH}"
echo "Tamanho mínimo: ${RD_OPTION_MIN_SIZE:-100M}"
echo "Idade mínima: ${RD_OPTION_FILE_AGE:-7d}"

# Criar arquivo de log
LOG_FILE="/var/log/results/disk-cleanup-$(date +%s).log"
mkdir -p /var/log/results

{
  echo "================================================================="
  echo "           RELATÓRIO DE LIMPEZA DE DISCO (SIMULAÇÃO)"
  echo "================================================================="
  echo "ALERTA ID: ${RD_OPTION_ALERT_ID:-N/A}"
  echo "CAMINHO: ${RD_OPTION_PATH}"
  echo "DATA/HORA: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "================================================================="
  echo
  echo "ANÁLISE PRÉ-LIMPEZA:"
  echo "-----------------------------------------------------------------"
  echo "Espaço em disco antes da limpeza:"
  df -h | grep -E "(Filesystem|${RD_OPTION_PATH})"
  echo
  echo "Arquivos mais volumosos encontrados:"
  echo "  - /var/log/syslog: 256MB (últimas modificação: 15 dias atrás)"
  echo "  - /var/log/mongodb/mongodb.log: 512MB (última modificação: 30 dias atrás)"
  echo "  - /var/cache/apt/archives/*.deb: 350MB total (diversos arquivos)"
  echo
  echo "AÇÕES EXECUTADAS:"
  echo "-----------------------------------------------------------------"
  echo "✓ Removidos 15 arquivos de log com mais de ${RD_OPTION_FILE_AGE:-7d} dias"
  echo "✓ Limpo cache de pacotes temporários"
  echo "✓ Compactados logs antigos"
  echo
  echo "RESULTADO:"
  echo "-----------------------------------------------------------------"
  echo "Espaço em disco após limpeza (simulação):"
  echo "Filesystem      Size  Used Avail Use% Mounted on"
  echo "/dev/sda1        50G   23G   27G  45% ${RD_OPTION_PATH}"
  echo
  echo "Espaço recuperado: 1.2GB"
  echo
  echo "================================================================="
} | tee "$LOG_FILE"

# Desativar o problema simulado
echo "30" > /etc/zabbix/scripts/simulate_disk_full.txt
echo "Problema de disco simulado DESATIVADO após limpeza"

# Simulação bem-sucedida
exit 0