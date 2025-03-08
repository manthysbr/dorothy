#!/bin/bash
# Script para simulação de envio de notificações

# Parâmetros recebidos do Rundeck
TEAM="$RD_OPTION_TEAM"
PRIORITY="${RD_OPTION_PRIORITY:-medium}"
MESSAGE="$RD_OPTION_MESSAGE"
LOG_FILE="/var/log/results/notification-$(date +%s).log"

{
    echo "================================================================="
    echo "                   NOTIFICAÇÃO ENVIADA"
    echo "================================================================="
    echo "DATA/HORA: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "ALERTA ID: ${RD_JOB_EXECID:-desconhecido}"
    echo "================================================================="
    echo
    echo "DETALHES DA NOTIFICAÇÃO:"
    echo "-----------------------------------------------------------------"
    echo "Equipe: ${TEAM:-'Todas as equipes'}"
    echo "Prioridade: $PRIORITY"
    echo "Mensagem: $MESSAGE"
    echo

    # Simulação de ação tomada
    case "$PRIORITY" in
        high|critical)
            EMOJI="🔴"
            echo "$EMOJI AÇÃO: Ticket #INC-$(date +%s | cut -c 6-10) de alta prioridade criado no ServiceDesk"
            echo "$EMOJI AÇÃO: Notificação SMS enviada para os responsáveis de plantão"
            echo "$EMOJI AÇÃO: Alert publicado no canal #incidentes-criticos no Slack"
            ;;
        medium)
            EMOJI="🟡"
            echo "$EMOJI AÇÃO: Ticket #INC-$(date +%s | cut -c 6-10) de média prioridade criado no ServiceDesk"
            echo "$EMOJI AÇÃO: Alerta enviado para o canal adequado no Slack"
            ;;
        low|info)
            EMOJI="🔵"
            echo "$EMOJI AÇÃO: Registro #LOG-$(date +%s | cut -c 6-10) adicionado ao log de eventos"
            echo "$EMOJI AÇÃO: Notificação enviada por email para a equipe responsável"
            ;;
    esac
    
    echo
    echo "ENCAMINHAMENTOS:"
    echo "-----------------------------------------------------------------"
    
    # Determinar para quem encaminhar com base na equipe e prioridade
    if [[ -z "$TEAM" || "$TEAM" == "operations" ]]; then
        echo "✓ Equipe de Operações: Notificação enviada via Slack e email"
        echo "  • Contatos: equipe-operacoes@empresa.com"
        echo "  • Canal: #operacoes-ti"
    fi
    
    if [[ -z "$TEAM" || "$TEAM" == "development" ]]; then
        echo "✓ Equipe de Desenvolvimento: Notificação enviada via Slack e email"
        echo "  • Contatos: desenvolvedores@empresa.com"
        echo "  • Canal: #dev-alerts"
    fi
    
    if [[ -z "$TEAM" || "$TEAM" == "security" ]]; then
        echo "✓ Equipe de Segurança: Notificação enviada via Slack e email"
        echo "  • Contatos: seguranca@empresa.com"
        echo "  • Canal: #security-alerts"
    fi
    
    # Para alta prioridade, registrar em sistemas adicionais
    if [[ "$PRIORITY" == "high" || "$PRIORITY" == "critical" ]]; then
        echo "✓ Status do incidente visível no dashboard de operações"
        echo "✓ Alerta SMS enviado para coordenadores: +5511XXXXXXXXXX, +5511987654321"
        echo "✓ Incidente agendado para discussão na próxima reunião de retrospectiva"
    fi
    
    echo
    echo "PRÓXIMOS PASSOS RECOMENDADOS:"
    echo "-----------------------------------------------------------------"
    if [[ "$PRIORITY" == "high" || "$PRIORITY" == "critical" ]]; then
        echo "1. Verificar imediatamente o problema reportado"
        echo "2. Escalar para especialistas se não for resolvido em 30 minutos"
        echo "3. Atualizar o status do incidente a cada hora até resolução"
        echo "4. Documentar todas as ações no ticket #INC-$(date +%s | cut -c 6-10)"
    elif [[ "$PRIORITY" == "medium" ]]; then
        echo "1. Analisar o problema dentro das próximas 4 horas"
        echo "2. Verificar se há incidentes similares anteriores"
        echo "3. Documentar soluções aplicadas no ticket #INC-$(date +%s | cut -c 6-10)"
    else
        echo "1. Agendar análise do problema para o próximo dia útil"
        echo "2. Verificar se há padrões recorrentes neste tipo de alerta"
    fi
    
    echo
    echo "================================================================="
    echo "                      FIM DA NOTIFICAÇÃO"
    echo "================================================================="
} | tee -a "$LOG_FILE"

# Criar link para o último log para fácil acesso
ln -sf "$LOG_FILE" /var/log/results/latest-notification.log

echo "Script executado com sucesso. Log completo: $LOG_FILE"
exit 0