#!/bin/bash
# Simula serviço parado

# Simulamos um serviço fictício chamado "nginx"
if [ -f "/tmp/simulate_service_down" ]; then
    echo "0"  # 0 = serviço parado
else
    echo "1"  # 1 = serviço em execução
fi