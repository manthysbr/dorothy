#!/bin/bash
set -e

# Garantir que o diretório do PID existe e tem permissões corretas
mkdir -p /var/run/zabbix
chown -R zabbix:zabbix /var/run/zabbix
chmod 755 /var/run/zabbix

# Copiar scripts se eles existirem no volume montado
if [ -d "/etc/zabbix/scripts/scripts" ]; then
    chmod +x /etc/zabbix/scripts/scripts/*.sh 2>/dev/null || true
fi

# Iniciar o agente Zabbix em primeiro plano
exec zabbix_agent2 -c /etc/zabbix/zabbix_agent2.conf -f