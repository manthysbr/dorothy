#!/bin/bash
# Script para analisar processos consumindo recursos

# Parâmetros recebidos do Rundeck
RESOURCE_TYPE="$RD_OPTION_RESOURCE_TYPE"
TOP_COUNT="${RD_OPTION_TOP_COUNT:-5}"

echo "=== Iniciando análise de processos ==="
echo "Tipo de recurso: $RESOURCE_TYPE"
echo "Quantidade de processos: $TOP_COUNT"

# Validar parâmetros
if [ -z "$RESOURCE_TYPE" ]; then
    echo "ERRO: Tipo de recurso não especificado"
    exit 1
fi

case "$RESOURCE_TYPE" in
    cpu)
        echo -e "\n=== Top $TOP_COUNT processos consumindo CPU ==="
        ps aux --sort=-%cpu | head -n $((TOP_COUNT + 1))
        
        echo -e "\n=== Estatísticas gerais de CPU ==="
        top -b -n 1 | head -n 5
        
        echo -e "\n=== Carga do sistema ==="
        uptime
        ;;
        
    memory)
        echo -e "\n=== Top $TOP_COUNT processos consumindo memória ==="
        ps aux --sort=-%mem | head -n $((TOP_COUNT + 1))
        
        echo -e "\n=== Estatísticas gerais de memória ==="
        free -h
        ;;
        
    io)
        echo -e "\n=== Top $TOP_COUNT processos com maior I/O ==="
        if command -v iotop &> /dev/null; then
            iotop -b -n 1 -o | head -n $((TOP_COUNT + 2))
        else
            echo "AVISO: iotop não está instalado. Usando iostat."
            iostat -xz 1 2
        fi
        
        echo -e "\n=== Estatísticas de disco ==="
        df -h
        ;;
        
    *)
        echo "ERRO: Tipo de recurso '$RESOURCE_TYPE' não reconhecido"
        echo "Tipos válidos: cpu, memory, io"
        exit 1
        ;;
esac

echo -e "\n=== Recomendações ==="
case "$RESOURCE_TYPE" in
    cpu)
        echo "1. Considere reiniciar os processos com consumo elevado de CPU"
        echo "2. Verifique se há processos zumbis ou em deadlock"
        echo "3. Avalie a necessidade de escalar verticalmente (adicionar mais CPUs)"
        ;;
        
    memory)
        echo "1. Verifique se há vazamentos de memória nos processos listados"
        echo "2. Considere aumentar o swap ou adicionar mais RAM"
        echo "3. Reinicie aplicações com consumo elevado de memória"
        ;;
        
    io)
        echo "1. Verifique se há processos realizando E/S excessiva"
        echo "2. Considere otimizar operações de disco das aplicações"
        echo "3. Avalie usar discos mais rápidos ou adicionar cache"
        ;;
esac

echo -e "\n=== Análise de processos concluída ==="
exit 0