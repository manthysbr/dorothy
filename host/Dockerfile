FROM ubuntu:22.04

# Evitar diálogos interativos durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# Instalar repositórios e dependências
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    ca-certificates \
    lsb-release \
    stress-ng \
    procps \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Adicionar repositório do Zabbix
RUN wget -q https://repo.zabbix.com/zabbix/7.0/ubuntu/pool/main/z/zabbix-release/zabbix-release_7.0-1+ubuntu22.04_all.deb \
    && dpkg -i zabbix-release_7.0-1+ubuntu22.04_all.deb \
    && apt-get update \
    && apt-get install -y zabbix-agent2 \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório para scripts
RUN mkdir -p /etc/zabbix/scripts && chmod 755 /etc/zabbix/scripts

# Expor porta do agente Zabbix
EXPOSE 10050

# Comando de inicialização
CMD ["zabbix_agent2", "-f", "-c", "/etc/zabbix/zabbix_agent2.conf"]