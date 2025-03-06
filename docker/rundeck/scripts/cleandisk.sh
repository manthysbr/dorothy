#!/bin/bash
# Script para limpeza de disco em servidores

# Parâmetros recebidos do Rundeck
PATH_TO_CLEAN="$RD_OPTION_PATH"
MIN_SIZE="${RD_OPTION_MIN_SIZE:-100M}"
FILE_AGE="${RD_OPTION_FILE_AGE:-7d}"

echo "=== Iniciando limpeza de disco ==="
echo "Caminho: $PATH_TO_CLEAN"
echo "Tamanho mínimo: $MIN_SIZE"
echo "Idade mínima: $FILE_AGE"

# Validar parâmetros
if [ -z "$PATH_TO_CLEAN" ]; then
    echo "ERRO: Caminho não especificado"
    exit 1
fi

# Verificar se o caminho existe
if [ ! -d "$PATH_TO_CLEAN" ]; then
    echo "ERRO: Diretório $PATH_TO_CLEAN não encontrado"
    exit 1
fi

# Mostrar espaço antes da limpeza
echo -e "\nEspaço em disco antes da limpeza:"
df -h "$PATH_TO_CLEAN"

# Encontrar arquivos grandes e antigos
echo -e "\nEncontrando arquivos para remoção..."

# Converter FILE_AGE para o formato correto do find
if [[ "$FILE_AGE" =~ ([0-9]+)d ]]; then
    DAYS=${BASH_REMATCH[1]}
    AGE_PARAM="-mtime +$DAYS"
elif [[ "$FILE_AGE" =~ ([0-9]+)h ]]; then
    HOURS=${BASH_REMATCH[1]}
    # Converter horas para minutos para o find
    MINUTES=$((HOURS * 60))
    AGE_PARAM="-mmin +$MINUTES"
else
    # Padrão: 7 dias
    AGE_PARAM="-mtime +7"
fi

# Listar arquivos que seriam removidos
echo "Arquivos que serão removidos:"
find "$PATH_TO_CLEAN" -type f $AGE_PARAM -size "+$MIN_SIZE" -exec ls -lh {} \; | head -10

# Contar quantos arquivos serão removidos
TOTAL_FILES=$(find "$PATH_TO_CLEAN" -type f $AGE_PARAM -size "+$MIN_SIZE" | wc -l)
echo -e "\nTotal de arquivos a remover: $TOTAL_FILES"

# Remover arquivos
echo -e "\nRemovendo arquivos..."
find "$PATH_TO_CLEAN" -type f $AGE_PARAM -size "+$MIN_SIZE" -delete

# Remover diretórios vazios
echo -e "\nRemovendo diretórios vazios..."
find "$PATH_TO_CLEAN" -type d -empty -delete

# Mostrar espaço após a limpeza
echo -e "\nEspaço em disco após limpeza:"
df -h "$PATH_TO_CLEAN"

echo -e "\n=== Limpeza de disco concluída ==="
exit 0