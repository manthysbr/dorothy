#!/bin/bash
# Script para enviar notificações para equipes

# Parâmetros recebidos do Rundeck
TEAM="$RD_OPTION_TEAM"
PRIORITY="${RD_OPTION_PRIORITY:-medium}"
MESSAGE="$RD_OPTION_MESSAGE"

echo "=== Enviando notificação ==="
echo "Equipe: ${TEAM:-todas}"
echo "Prioridade: $PRIORITY"
echo "Mensagem: $MESSAGE"

# Validar parâmetros
if [ -z "$MESSAGE" ]; then
    echo "ERRO: Mensagem não especificada"
    exit 1
fi

# Simular envio de notificação
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
NOTIFICATION_ID=$(date +%s)

case "$PRIORITY" in
    high|critical)
        EMOJI="🔴"
        ;;
    medium|warning)
        EMOJI="🟡"
        ;;
    low|info)
        EMOJI="🔵"
        ;;
    *)
        EMOJI="ℹ️"
        ;;
esac

echo -e "\n$EMOJI Notificação [$NOTIFICATION_ID] - $TIMESTAMP"
echo -e "Para: ${TEAM:-todas as equipes}"
echo -e "Prioridade: $PRIORITY"
echo -e "Mensagem: $MESSAGE"

# Simular integração com diferentes canais
echo -e "\nCanais de notificação:"

if [ -z "$TEAM" ] || [ "$TEAM" = "operations" ]; then
    echo "✓ Enviado para canal #operacoes no Slack"
fi

if [ -z "$TEAM" ] || [ "$TEAM" = "development" ]; then
    echo "✓ Enviado para canal #desenvolvimento no Slack"
fi

if [ -z "$TEAM" ] || [ "$TEAM" = "security" ]; then
    echo "✓ Enviado para canal #seguranca no Slack"
fi

if [ "$PRIORITY" = "high" ] || [ "$PRIORITY" = "critical" ]; then
    echo "✓ Enviado alerta SMS para responsáveis"
    echo "✓ Criado ticket de alta prioridade no sistema de incidentes"
fi

echo -e "\n=== Notificação enviada com sucesso ==="
exit 0