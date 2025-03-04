import asyncio
import json
import httpx
import sys
import os
import time

# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Exemplo de payload simulando alerta do Zabbix
EXAMPLE_PAYLOADS = {
    "disk_full": {
        "event_id": "12345",
        "host": "web-server-01",
        "problem": "Espaço em disco crítico: 95% utilizado em /var",
        "severity": "high",
        "timestamp": int(time.time()),
        "item_id": "54321",
        "trigger_id": "98765",
        "status": "PROBLEM",
        "details": {
            "free_space": "500MB",
            "total_space": "10GB",
            "filesystem": "/var",
            "mount_point": "/var"
        },
        "tags": [
            {"tag": "service", "value": "web"},
            {"tag": "environment", "value": "production"}
        ]
    },
    "service_down": {
        "event_id": "12346",
        "host": "app-server-02",
        "problem": "Serviço nginx parado",
        "severity": "high",
        "timestamp": int(time.time()),
        "status": "PROBLEM",
        "details": {
            "service_name": "nginx",
            "last_seen": "10 minutes ago",
            "exit_code": "1"
        },
        "tags": [
            {"tag": "service", "value": "web"},
            {"tag": "component", "value": "nginx"}
        ]
    },
    "high_cpu": {
        "event_id": "12347",
        "host": "db-server-01",
        "problem": "Alta utilização de CPU: 95% por mais de 15 minutos",
        "severity": "warning",
        "timestamp": int(time.time()),
        "status": "PROBLEM",
        "details": {
            "cpu_usage": "95%",
            "duration": "15 minutes",
            "top_processes": [
                "mysql: 45%",
                "system: 30%",
                "user: 20%"
            ]
        },
        "tags": [
            {"tag": "service", "value": "database"},
            {"tag": "component", "value": "mysql"}
        ]
    }
}


async def test_api(alert_type="disk_full", api_url="http://localhost:8000"):
    """
    Testa a API Dorothy enviando um alerta simulado do Zabbix.
    
    Args:
        alert_type: Tipo de alerta para enviar (disk_full, service_down, high_cpu)
        api_url: URL da API Dorothy
    """
    if alert_type not in EXAMPLE_PAYLOADS:
        print(f"Tipo de alerta '{alert_type}' não encontrado!")
        print(f"Tipos disponíveis: {', '.join(EXAMPLE_PAYLOADS.keys())}")
        return
    
    payload = EXAMPLE_PAYLOADS[alert_type]
    endpoint = f"{api_url}/api/v1/zabbix/alert"
    
    print(f"Enviando alerta '{alert_type}' para {endpoint}...")
    print("-" * 50)
    print(f"Payload:\n{json.dumps(payload, indent=2)}")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            response = await client.post(
                endpoint,
                json=payload,
                timeout=30.0
            )
            elapsed = time.time() - start_time
            
            print(f"Status: {response.status_code}")
            print(f"Tempo de resposta: {elapsed:.2f}s")
            print("-" * 50)
            
            if response.status_code == 200:
                result = response.json()
                print("Resposta da API:")
                print(json.dumps(result, indent=2))
            else:
                print(f"Erro! Status: {response.status_code}")
                print(response.text)
    
    except Exception as e:
        print(f"Erro ao fazer requisição: {str(e)}")


if __name__ == "__main__":
    # Obter tipo de alerta da linha de comando, se fornecido
    alert_type = sys.argv[1] if len(sys.argv) > 1 else "disk_full"
    
    # URL da API (permite especificar através da variável de ambiente)
    api_url = os.getenv("DOROTHY_API_URL", "http://localhost:8000")
    
    print(f"=== Testando API Dorothy com alerta: {alert_type} ===")
    asyncio.run(test_api(alert_type, api_url))