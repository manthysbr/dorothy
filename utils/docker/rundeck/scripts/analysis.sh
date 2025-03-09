#!/bin/bash
# Script para simulação de análise de processos

# Parâmetros recebidos do Rundeck
RESOURCE_TYPE="$RD_OPTION_RESOURCE_TYPE"
TOP_COUNT="${RD_OPTION_TOP_COUNT:-5}"
LOG_FILE="/var/log/results/analysis-$(date +%s).log"

{
    echo "================================================================="
    echo "                 ANÁLISE DE PROCESSOS EXECUTADA"
    echo "================================================================="
    echo "DATA/HORA: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "ALERTA ID: ${RD_JOB_EXECID:-desconhecido}"
    echo "================================================================="
    echo
    echo "PARÂMETROS:"
    echo "-----------------------------------------------------------------"
    echo "Tipo de recurso: $RESOURCE_TYPE"
    echo "Quantidade: $TOP_COUNT"
    echo
    
    echo "RESULTADO DA ANÁLISE:"
    echo "-----------------------------------------------------------------"
    
    case "$RESOURCE_TYPE" in
        cpu)
            echo "TOP PROCESSOS CONSUMINDO CPU:"
            echo "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND"
            echo "root      1234 85.2  5.2 854096 54892 ?        R    10:15   22:30 /usr/bin/aplicacao-problema"
            echo "mysql     2345 25.1  8.7 1258216 89120 ?       S    09:24   12:22 /usr/sbin/mysqld"
            echo "www-data  3456 15.0  3.4 720012 34524 ?        S    10:05   05:45 /usr/sbin/apache2"
            echo "mongodb   4567 12.3  6.8 950452 68234 ?        S    09:30   07:15 /usr/bin/mongod"
            echo "root      5678  8.5  1.2 125624 12450 ?        S    08:45   04:22 /usr/sbin/rsyslogd"
            
            echo
            echo "ESTATÍSTICAS GERAIS DE CPU:"
            echo "top - $(date '+%H:%M:%S') up 15:24,  2 users,  load average: 2.45, 2.15, 1.97"
            echo "Tasks: 258 total,   2 running, 256 sleeping,   0 stopped,   0 zombie"
            echo "%Cpu(s): 65.2 us, 12.5 sy,  0.0 ni, 18.2 id,  0.0 wa,  4.1 hi,  0.0 si,  0.0 st"
            ;;
        memory)
            echo "TOP PROCESSOS CONSUMINDO MEMÓRIA:"
            echo "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND"
            echo "java      1234 35.2 45.8 4854096 468924 ?      S    08:15   15:30 /usr/bin/java -Xmx2g -jar app.jar"
            echo "postgres  3456 12.3 22.4 2258216 229120 ?      S    09:24   08:22 /usr/lib/postgresql/13/bin/postgres"
            echo "www-data  5678  8.5 15.8 1720012 161524 ?      S    10:05   04:45 /usr/sbin/apache2"
            echo "root      9012  6.2 10.2 1050452 104234 ?      S    09:30   03:15 /usr/bin/containerapp"
            echo "redis     3344  2.5  5.5 425624 56450 ?        S    08:45   02:22 /usr/bin/redis-server"
            
            echo
            echo "ESTATÍSTICAS GERAIS DE MEMÓRIA:"
            echo "               total        used        free      shared  buff/cache   available"
            echo "Mem:          15.6Gi       12.3Gi       0.4Gi       1.4Gi       2.9Gi       1.9Gi"
            echo "Swap:          4.0Gi       1.2Gi       2.8Gi"
            ;;
        io)
            echo "TOP PROCESSOS COM MAIOR I/O:"
            echo "Current DISK READ:     125.4 K/s | Current DISK WRITE:    3452.6 K/s"
            echo "    TID  PRIO  USER     DISK READ  DISK WRITE  SWAPIN      IO    COMMAND"
            echo "   1234   BE   mysql      80.2 K/s   2240.8 K/s  0.0 %  12.4 % mysqld --innodb-buffer-pool-size=4G"
            echo "   3456   BE   postgres   20.4 K/s    890.2 K/s  0.0 %   8.2 % postgres: writer process"
            echo "   5678   BE   www-data   15.8 K/s    160.4 K/s  0.0 %   4.5 % apache2 -k start"
            echo "   9012   BE   mongodb     5.2 K/s    120.6 K/s  0.0 %   3.8 % mongod --dbpath=/var/lib/mongodb"
            echo "   1122   BE   root        3.8 K/s     40.6 K/s  0.0 %   2.1 % dockerd"
            
            echo
            echo "ESTATÍSTICAS DE DISCO:"
            echo "Filesystem      Size  Used Avail Use% Mounted on"
            echo "/dev/sda1        50G   42G    8G  84% /"
            echo "/dev/sdb1       100G   75G   25G  75% /data"
            ;;
    esac
    
    echo
    echo "RECOMENDAÇÕES:"
    echo "-----------------------------------------------------------------"
    case "$RESOURCE_TYPE" in
        cpu)
            echo "1. Verificar o processo 'aplicacao-problema' (PID 1234) com consumo anormal de CPU (85.2%)"
            echo "2. Considerar reiniciar ou ajustar limites de recursos para este processo"
            echo "3. Verificar se o processo 'mysqld' (PID 2345) está com consultas pesadas em execução"
            echo "4. Analisar se há necessidade de escalabilidade vertical (mais CPU)"
            echo "5. Verificar se há processos em deadlock ou memory leak causando alto uso de CPU"
            ;;
        memory)
            echo "1. O processo Java (PID 1234) está usando 45.8% da memória disponível"
            echo "2. Verificar configurações de heap (-Xmx) da aplicação Java"
            echo "3. Analisar se há vazamento de memória no PostgreSQL (PID 3456)"
            echo "4. Considerar aumentar o swap ou adicionar mais memória física"
            echo "5. Verificar se o Apache (PID 5678) está com muitas conexões simultâneas"
            ;;
        io)
            echo "1. O processo MySQL (TID 1234) está causando alta E/S de disco"
            echo "2. Verificar queries pesadas ou índices ausentes no MySQL"
            echo "3. Considerar ajustar o innodb-buffer-pool-size para reduzir E/S"
            echo "4. Verificar se o PostgreSQL (TID 3456) está fazendo muitos checkpoints"
            echo "5. Avaliar a necessidade de discos mais rápidos ou storage SSD"
            ;;
    esac
    
    echo
    echo "================================================================="
    echo "                      ANÁLISE CONCLUÍDA"
    echo "================================================================="
} | tee -a "$LOG_FILE"

# Criar link para o último log para fácil acesso
ln -sf "$LOG_FILE" /var/log/results/latest-analysis.log

echo "Script executado com sucesso. Log completo: $LOG_FILE"
exit 0