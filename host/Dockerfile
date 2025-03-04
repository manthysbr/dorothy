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
    sysstat \
    iproute2 \
    iputils-ping \
    curl \
    python3 \
    python3-pip \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Adicionar repositório do Zabbix
RUN wget -q https://repo.zabbix.com/zabbix/7.0/ubuntu/pool/main/z/zabbix-release/zabbix-release_7.0-1+ubuntu22.04_all.deb \
    && dpkg -i zabbix-release_7.0-1+ubuntu22.04_all.deb \
    && apt-get update

# Instalar agente Zabbix
RUN apt-get install -y zabbix-agent2

# Criar diretório para scripts
RUN mkdir -p /etc/zabbix/scripts && chmod 755 /etc/zabbix/scripts

# Copiar scripts de simulação
COPY ./scripts/ /etc/zabbix/scripts/
RUN chmod +x /etc/zabbix/scripts/*.sh

# Adicionar configuração do agente
COPY ./zabbix_agent2.conf /etc/zabbix/zabbix_agent2.conf
COPY ./zabbix_agent2.d/ /etc/zabbix/zabbix_agent2.d/

# Expor porta do agente Zabbix
EXPOSE 10050

# Comando de inicialização
CMD ["zabbix_agent2", "-f", "-c", "/etc/zabbix/zabbix_agent2.conf"]