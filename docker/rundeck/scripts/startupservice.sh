#!/bin/bash
# Script para reiniciar serviços

# Parâmetros recebidos do Rundeck
SERVICE_NAME="$RD_OPTION_SERVICE_NAME"
FORCE="${RD_OPTION_FORCE:-false}"

echo "=== Iniciando reinicialização de serviço ==="
echo "Serviço: $SERVICE_NAME"
echo "Forçar: $FORCE"

# Validar parâmetros
if [ -z "$SERVICE_NAME" ]; then
    echo "ERRO: Nome do serviço não especificado"
    exit 1
fi

# Verificar se o serviço existe
if ! systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
    echo "AVISO: Serviço $SERVICE_NAME não encontrado como uma unidade systemd"
    # Tentar verificar usando service command para sistemas não-systemd
    if ! service --status-all 2>&1 | grep -q "$SERVICE_NAME"; then
        echo "ERRO: Serviço $SERVICE_NAME não encontrado no sistema"
        exit 1
    fi
fi

# Verificar status atual do serviço
echo -e "\nStatus atual do serviço:"
systemctl status "$SERVICE_NAME" || service "$SERVICE_NAME" status

# Reiniciar o serviço
echo -e "\nReiniciando serviço..."
if [ "$FORCE" = "true" ]; then
    echo "Reinício forçado solicitado"
    systemctl stop "$SERVICE_NAME" || service "$SERVICE_NAME" stop
    sleep 2
    systemctl start "$SERVICE_NAME" || service "$SERVICE_NAME" start
else
    systemctl restart "$SERVICE_NAME" || service "$SERVICE_NAME" restart
fi

# Verificar resultado
if [ $? -eq 0 ]; then
    echo -e "\nServiço reiniciado com sucesso"
    
    # Esperar um pouco para o serviço iniciar completamente
    sleep 3
    
    # Mostrar novo status
    echo -e "\nNovo status do serviço:"
    systemctl status "$SERVICE_NAME" || service "$SERVICE_NAME" status
    
    echo -e "\n=== Reinicialização concluída com sucesso ==="
    exit 0
else
    echo -e "\nERRO: Falha ao reiniciar o serviço"
    echo -e "\n=== Reinicialização falhou ==="
    exit 1
fi