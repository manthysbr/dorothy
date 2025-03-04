#!/bin/bash

if [ -f "/tmp/simulate_disk_full" ]; then
    echo "5.0"
    # Cria um arquivo grande para simular disco cheio
    if [ ! -f "/tmp/bigfile" ]; then
        dd if=/dev/zero of=/tmp/bigfile bs=1M count=500 > /dev/null 2>&1 &
    fi
else
    # Espaço livre normal (entre 60-80%)
    echo $(( (RANDOM % 20) + 60 )).$(( RANDOM % 10 ))
    # Remove arquivo grande se existir
    rm -f /tmp/bigfile
fi