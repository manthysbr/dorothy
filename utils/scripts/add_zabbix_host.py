#!/usr/bin/env python3
"""
Script para adicionar automaticamente o host simulador ao Zabbix
"""
import sys
import time
import argparse
import requests
from pyzabbix import ZabbixAPI

# Desabilitar avisos de SSL para ambientes de desenvolvimento
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def add_simulator_host(zabbix_url, username, password):
    """
    Adiciona o host simulador ao Zabbix.
    """
    print(f"Conectando ao Zabbix em {zabbix_url}...")
    
    try:
        # Conectar à API do Zabbix
        zapi = ZabbixAPI(zabbix_url)
        zapi.login(username, password)
        print(f"Conectado ao Zabbix API v.{zapi.api_version()}")
        
        # Verificar se o host já existe
        existing = zapi.host.get(filter={"host": "Problem-Simulator"})
        if existing:
            print("Host 'Problem-Simulator' já existe. Nenhuma ação necessária.")
            return
        
        # Obter o ID do grupo "Linux servers"
        groups = zapi.hostgroup.get(filter={"name": "Linux servers"})
        if not groups:
            print("Criando grupo 'Linux servers'...")
            group_id = zapi.hostgroup.create(name="Linux servers")["groupids"][0]
        else:
            group_id = groups[0]["groupid"]
        
        # Obter o ID do template "Template OS Linux by Zabbix agent"
        templates = zapi.template.get(filter={"host": "Template OS Linux by Zabbix agent"})
        if not templates:
            print("Erro: Template 'Template OS Linux by Zabbix agent' não encontrado.")
            return
        template_id = templates[0]["templateid"]
        
        # Adicionar o host
        host = {
            "host": "Problem-Simulator",
            "interfaces": [
                {
                    "type": 1,  # 1 = agent
                    "main": 1,  # interface principal
                    "useip": 1,  # usar IP em vez de DNS
                    "ip": "zabbix-agent-simulator",  # nome do container
                    "dns": "",
                    "port": "10050"
                }
            ],
            "groups": [
                {
                    "groupid": group_id
                }
            ],
            "templates": [
                {
                    "templateid": template_id
                }
            ],
            "inventory_mode": 0,
            "description": "Host para simulação de problemas",
            "inventory": {
                "type": "Virtual machine",
                "name": "Simulador de Problemas"
            }
        }
        
        result = zapi.host.create(**host)
        print(f"Host 'Problem-Simulator' adicionado com ID: {result['hostids'][0]}")
        
        # Adicionar itens personalizados
        add_custom_items(zapi, result["hostids"][0])
        
    except Exception as e:
        print(f"Erro ao adicionar host: {str(e)}")
        sys.exit(1)
    finally:
        pass


def add_custom_items(zapi, host_id):
    """
    Adiciona itens personalizados ao host.
    
    Args:
        zapi: Objeto ZabbixAPI conectado
        host_id: ID do host
    """
    try:
        # Item para CPU
        cpu_item = {
            "name": "Simulação de carga de CPU",
            "key_": "custom.cpu_load",
            "hostid": host_id,
            "type": 0,  # 0 = Zabbix agent
            "value_type": 0,  # 0 = numérico float
            "delay": "30s",
            "history": "7d",
            "trends": "90d",
            "units": "%",
            "description": "Simulação de carga de CPU para testes"
        }
        zapi.item.create(**cpu_item)
        print("Item 'Simulação de carga de CPU' criado")
        
        # Item para disco
        disk_item = {
            "name": "Simulação de espaço livre em disco",
            "key_": "custom.disk_free",
            "hostid": host_id,
            "type": 0,  # 0 = Zabbix agent
            "value_type": 0,  # 0 = numérico float
            "delay": "30s",
            "history": "7d",
            "trends": "90d",
            "units": "%",
            "description": "Simulação de espaço livre em disco para testes"
        }
        zapi.item.create(**disk_item)
        print("Item 'Simulação de espaço livre em disco' criado")
        
        # Item para memória
        memory_item = {
            "name": "Simulação de uso de memória",
            "key_": "custom.memory_usage",
            "hostid": host_id,
            "type": 0,  # 0 = Zabbix agent
            "value_type": 0,  # 0 = numérico float
            "delay": "30s",
            "history": "7d",
            "trends": "90d",
            "units": "%",
            "description": "Simulação de uso de memória para testes"
        }
        zapi.item.create(**memory_item)
        print("Item 'Simulação de uso de memória' criado")
        
        # Item para serviço
        service_item = {
            "name": "Simulação de serviço",
            "key_": "custom.service_status",
            "hostid": host_id,
            "type": 0,  # 0 = Zabbix agent
            "value_type": 3,  # 3 = numérico inteiro
            "delay": "30s",
            "history": "7d",
            "trends": "90d",
            "description": "Simulação de status de serviço para testes"
        }
        zapi.item.create(**service_item)
        print("Item 'Simulação de serviço' criado")
        
        # Triggers para os itens
        create_triggers(zapi, host_id)
        
    except Exception as e:
        print(f"Erro ao adicionar itens personalizados: {str(e)}")


def create_triggers(zapi, host_id):
    """
    Cria triggers para os itens personalizados.
    
    Args:
        zapi: Objeto ZabbixAPI conectado
        host_id: ID do host
    """
    try:
        # Buscar os itens
        items = zapi.item.get(
            hostids=host_id,
            search={"key_": "custom."},
            searchByAny=True
        )
        
        item_dict = {}
        for item in items:
            if "custom.cpu_load" in item["key_"]:
                item_dict["cpu"] = item["itemid"]
            elif "custom.disk_free" in item["key_"]:
                item_dict["disk"] = item["itemid"]
            elif "custom.memory_usage" in item["key_"]:
                item_dict["memory"] = item["itemid"]
            elif "custom.service_status" in item["key_"]:
                item_dict["service"] = item["itemid"]
        
        # Trigger para CPU alta
        if "cpu" in item_dict:
            cpu_trigger = {
                "description": "Alta utilização de CPU no servidor simulado",
                "expression": f"last(/Problem-Simulator/custom.cpu_load)>90",
                "priority": 4,  # 4 = high
                "status": 0,  # 0 = habilitado
                "tags": [
                    {
                        "tag": "component",
                        "value": "cpu"
                    }
                ]
            }
            zapi.trigger.create(**cpu_trigger)
            print("Trigger para CPU alta criada")
        
        # Trigger para disco cheio
        if "disk" in item_dict:
            disk_trigger = {
                "description": "Espaço em disco crítico no servidor simulado",
                "expression": f"last(/Problem-Simulator/custom.disk_free)<10",
                "priority": 4,  # 4 = high
                "status": 0,  # 0 = habilitado
                "tags": [
                    {
                        "tag": "component",
                        "value": "disk"
                    }
                ]
            }
            zapi.trigger.create(**disk_trigger)
            print("Trigger para disco cheio criada")
        
        # Trigger para memória alta
        if "memory" in item_dict:
            memory_trigger = {
                "description": "Alta utilização de memória no servidor simulado",
                "expression": f"last(/Problem-Simulator/custom.memory_usage)>85",
                "priority": 3,  # 3 = average
                "status": 0,  # 0 = habilitado
                "tags": [
                    {
                        "tag": "component",
                        "value": "memory"
                    }
                ]
            }
            zapi.trigger.create(**memory_trigger)
            print("Trigger para memória alta criada")
        
        # Trigger para serviço parado
        if "service" in item_dict:
            service_trigger = {
                "description": "Serviço parado no servidor simulado",
                "expression": f"last(/Problem-Simulator/custom.service_status)=0",
                "priority": 4,  # 4 = high
                "status": 0,  # 0 = habilitado
                "tags": [
                    {
                        "tag": "component",
                        "value": "service"
                    }
                ]
            }
            zapi.trigger.create(**service_trigger)
            print("Trigger para serviço parado criada")
        
    except Exception as e:
        print(f"Erro ao criar triggers: {str(e)}")


def wait_for_zabbix(zabbix_url, max_retries=30, retry_interval=10):
    """
    Aguarda até que a API do Zabbix esteja disponível.
    
    Args:
        zabbix_url: URL da API do Zabbix
        max_retries: Número máximo de tentativas
        retry_interval: Intervalo entre tentativas em segundos
    """
    print(f"Aguardando o Zabbix estar disponível...")
    
    for i in range(max_retries):
        try:
            response = requests.get(
                zabbix_url.replace('api_jsonrpc.php', ''),
                verify=False,
                timeout=5
            )
            if response.status_code == 200:
                print("Zabbix disponível! Continuando...")
                time.sleep(5)  # Aguarda mais um pouco para garantir
                return True
        except Exception:
            pass
        
        print(f"Tentativa {i+1}/{max_retries} - Aguardando Zabbix...")
        time.sleep(retry_interval)
    
    print("Erro: Zabbix não ficou disponível no tempo esperado.")
    return False


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Adiciona o host simulador ao Zabbix'
    )
    parser.add_argument(
        '--zabbix-url',
        default='http://localhost:8080/api_jsonrpc.php',
        help='URL da API do Zabbix (padrão: http://localhost:8080/api_jsonrpc.php)'
    )
    parser.add_argument(
        '--username',
        default='Admin',
        help='Nome de usuário do Zabbix (padrão: Admin)'
    )
    parser.add_argument(
        '--password',
        default='zabbix',
        help='Senha do Zabbix (padrão: zabbix)'
    )
    
    args = parser.parse_args()
    
    # Aguardar que o Zabbix esteja disponível
    if wait_for_zabbix(args.zabbix_url):
        # Adicionar host simulador
        add_simulator_host(
            args.zabbix_url,
            args.username,
            args.password
        )


if __name__ == "__main__":
    main()