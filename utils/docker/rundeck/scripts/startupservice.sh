#!/bin/bash
# Script para simulação de reinicialização de serviço

# Parâmetros recebidos do Rundeck
SERVICE_NAME="$RD_OPTION_SERVICE_NAME"
FORCE="${RD_OPTION_FORCE:-false}"
LOG_FILE="/var/log/results/service-restart-$(date +%s).log"

{
    echo "================================================================="
    echo "               REINICIALIZAÇÃO DE SERVIÇO EXECUTADA"
    echo "================================================================="
    echo "DATA/HORA: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "ALERTA ID: ${RD_JOB_EXECID:-desconhecido}"
    echo "================================================================="
    echo
    echo "PARÂMETROS:"
    echo "-----------------------------------------------------------------"
    echo "Serviço: $SERVICE_NAME"
    echo "Reinício forçado: $FORCE"
    echo
    
    echo "ESTADO INICIAL:"
    echo "-----------------------------------------------------------------"
    echo "● $SERVICE_NAME.service - $SERVICE_NAME Service"
    echo "   Loaded: loaded (/lib/systemd/system/$SERVICE_NAME.service; enabled; vendor preset: enabled)"
    echo "   Active: failed (Result: exit-code) since $(date -d '5 minutes ago' '+%Y-%m-%d %H:%M:%S')"
    echo "  Process: 1234 ExecStart=/usr/bin/$SERVICE_NAME (code=exited, status=1)"
    echo "    Tasks: 0 (limit: 4915)"
    echo "   Memory: 0B"
    echo "   CGroup: /system.slice/$SERVICE_NAME.service"
    echo
    
    echo "LOGS DO SERVIÇO:"
    echo "-----------------------------------------------------------------"
    echo "$(date -d '5 minutes ago' '+%b %d %H:%M:%S') server $SERVICE_NAME[1234]: Erro: falha ao conectar ao banco de dados"
    echo "$(date -d '5 minutes ago' '+%b %d %H:%M:%S') server $SERVICE_NAME[1234]: Erro crítico durante inicialização"
    echo "$(date -d '5 minutes ago' '+%b %d %H:%M:%S') server systemd[1]: $SERVICE_NAME.service: Failed with result 'exit-code'"
    echo
    
    echo "AÇÃO EXECUTADA:"
    echo "-----------------------------------------------------------------"
    if [ "$FORCE" = "true" ]; then
        echo "🔄 Executando parada forçada do serviço: systemctl stop $SERVICE_NAME --force"
        sleep 1
        echo "✅ Serviço parado"
        sleep 1
        echo "🔄 Iniciando o serviço: systemctl start $SERVICE_NAME"
    else
        echo "🔄 Reiniciando o serviço: systemctl restart $SERVICE_NAME"
    fi
    
    echo
    sleep 2
    
    echo "RESULTADO:"
    echo "-----------------------------------------------------------------"
    echo "● $SERVICE_NAME.service - $SERVICE_NAME Service"
    echo "   Loaded: loaded (/lib/systemd/system/$SERVICE_NAME.service; enabled; vendor preset: enabled)"
    echo "   Active: active (running) since $(date '+%Y-%m-%d %H:%M:%S')"
    echo "  Process: 2468 ExecStart=/usr/bin/$SERVICE_NAME (code=running)"
    echo "    Tasks: 12 (limit: 4915)"
    echo "   Memory: 48.2M"
    echo "   CGroup: /system.slice/$SERVICE_NAME.service"
    echo
    echo "$(date '+%b %d %H:%M:%S') server $SERVICE_NAME[2468]: Inicializando $SERVICE_NAME..."
    echo "$(date '+%b %d %H:%M:%S') server $SERVICE_NAME[2468]: Conexão com banco de dados estabelecida"
    echo "$(date '+%b %d %H:%M:%S') server $SERVICE_NAME[2468]: Serviço iniciado e operacional"
    echo
    
    echo "================================================================="
    echo "                      OPERAÇÃO CONCLUÍDA"
    echo "================================================================="
} | tee -a "$LOG_FILE"

# Criar link para o último log para fácil acesso
ln -sf "$LOG_FILE" /var/log/results/latest-service-restart.log

echo "Script executado com sucesso. Log completo: $LOG_FILE"
exit 0