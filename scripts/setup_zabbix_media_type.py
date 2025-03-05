#!/usr/bin/env python3
"""
Script para configurar automaticamente o tipo de mídia WebHook no Zabbix
para enviar alertas para a API Dorothy.

Requisitos:
- pyzabbix==1.3.0
- requests>=2.28.0
"""
import sys
import time
import argparse
import requests
from pyzabbix import ZabbixAPI

# Desabilitar avisos de SSL para ambientes de desenvolvimento
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def setup_media_type(zabbix_url, username, password, api_url):
    """
    Configura o tipo de mídia webhook para Dorothy API no Zabbix.
    """
    print(f"Conectando ao Zabbix em {zabbix_url}...")
    try:
        zapi = ZabbixAPI(zabbix_url)
        zapi.login(username, password)
        print(f"Conectado ao Zabbix API v.{zapi.api_version()}")
        
        existing = zapi.mediatype.get(filter={"name": "Dorothy API"})
        if existing:
            print("Tipo de mídia 'Dorothy API' já existe. Atualizando...")
            media_id = existing[0]['mediatypeid']
            action = "atualizado"
        else:
            media_id = None
            action = "criado"
        
        params = {
            "endpoint": api_url + "/api/v1/zabbix/alert",
            "event_id": "{EVENT.ID}",
            "host": "{HOST.NAME}",
            "problem": "{TRIGGER.NAME}",
            "severity": "{EVENT.SEVERITY}",
            "status": "{EVENT.STATUS}",
            "timestamp": "{EVENT.TIME.EPOCH}",
            "details": {
                "ip": "{HOST.IP}",
                "description": "{TRIGGER.DESCRIPTION}",
                "item_value": "{ITEM.VALUE}",
                "item_id": "{ITEM.ID}"
            },
            "tags": [
                {"tag": "service", "value": "{INVENTORY.TAG}"},
                {"tag": "environment", "value": "{INVENTORY.ENV}"}
            ]
        }
        
        # Definição do tipo de mídia com estrutura correta para API v7.0
        mediatype = {
            "name": "Dorothy API",
            "type": 4,  # 4 = Webhook
            "status": 0,  # 0 = Habilitado
            "parameters": [
                {"name": "URL", "value": api_url + "/api/v1/zabbix/alert"},
                {"name": "HTTPProxy", "value": ""},
                {"name": "To", "value": "{ALERT.SENDTO}"},
                {"name": "Subject", "value": "{ALERT.SUBJECT}"},
                {"name": "Message", "value": "{ALERT.MESSAGE}"}
            ],
            "script": generate_webhook_script(params),
            "description": "Tipo de mídia para enviar alertas para a API Dorothy",
            # Estrutura correta conforme documentação do Zabbix 7.0
            "message_templates": [
                {
                    "eventsource": "0",  # 0 = triggers
                    "recovery": "0",     # 0 = problema
                    "subject": "Alerta: {EVENT.NAME}",
                    "message": generate_message_template()
                },
                {
                    "eventsource": "0",  # 0 = triggers
                    "recovery": "1",     # 1 = recuperação
                    "subject": "Resolução: {EVENT.NAME}",
                    "message": generate_message_template()
                },
                {
                    "eventsource": "0",  # 0 = triggers
                    "recovery": "2",     # 2 = atualização
                    "subject": "Atualização: {EVENT.NAME}",
                    "message": generate_message_template()
                }
            ]
        }
        
        if media_id:
            mediatype["mediatypeid"] = media_id
            result = zapi.mediatype.update(**mediatype)
        else:
            result = zapi.mediatype.create(**mediatype)
        
        print(f"Tipo de mídia 'Dorothy API' {action} com sucesso!")
        
        setup_action(zapi, result if not media_id else media_id)
        
    except Exception as e:
        print(f"Erro ao configurar tipo de mídia: {str(e)}")
        sys.exit(1)
    finally:
        pass


def generate_webhook_script(params):
    """
    Gera o script JavaScript do webhook.
    
    Args:
        params: Parâmetros a serem incluídos no payload
    
    Returns:
        Script JavaScript para o webhook
    """
    return """
var Dorothy = {
    params: {},
    
    setParams: function(params) {
        Dorothy.params = params;
    },
    
    request: function() {
        var params = Dorothy.params;
        var data = {};
        
        // Dados básicos do evento
        data.event_id = params.event_id;
        data.host = params.host;
        data.problem = params.problem;
        data.severity = params.severity;
        data.status = params.status;
        data.timestamp = parseInt(params.timestamp);
        
        // Adicionar detalhes se fornecidos
        if (params.details) {
            data.details = params.details;
        }
        
        // Adicionar tags se fornecidas
        if (params.tags && Array.isArray(params.tags)) {
            data.tags = params.tags;
        }
        
        // Converter para JSON
        var payload = JSON.stringify(data);
        
        // Configurar a requisição
        var request = new CurlHttpRequest();
        request.AddHeader('Content-Type: application/json');
        
        // Enviar a requisição
        var response = request.Post(params.endpoint, payload);
        Zabbix.Log(4, 'Dorothy WebHook: ' + payload);
        Zabbix.Log(4, 'Dorothy WebHook response: ' + response);
        
        // Retornar resposta
        try {
            var result = JSON.parse(response);
            return 'OK - Alerta enviado para Dorothy API';
        } catch (error) {
            if (response.indexOf('200') > -1) {
                return 'OK - Alerta enviado para Dorothy API';
            }
            return 'Erro ao enviar alerta: ' + response;
        }
    }
};

// Inicialização
try {
    var params = JSON.parse(value);
    Dorothy.setParams(params);
    return Dorothy.request();
} catch (error) {
    return 'Erro na execução do webhook: ' + error;
}
"""


def generate_message_template():
    """
    Gera o template de mensagem JSON para o alerta.
    
    Returns:
        Template JSON para o alerta
    """
    return """{
    "endpoint": "{{URL}}",
    "event_id": "{EVENT.ID}",
    "host": "{HOST.NAME}",
    "problem": "{TRIGGER.NAME}",
    "severity": "{EVENT.SEVERITY}",
    "status": "{EVENT.STATUS}",
    "timestamp": "{EVENT.TIME.EPOCH}",
    "details": {
        "ip": "{HOST.IP}",
        "description": "{TRIGGER.DESCRIPTION}",
        "item_value": "{ITEM.LASTVALUE}",
        "item_id": "{ITEM.ID}",
        "trigger_id": "{TRIGGER.ID}"
    },
    "tags": [
        {"tag": "service", "value": "{INVENTORY.TYPE}"},
        {"tag": "environment", "value": "{INVENTORY.TYPE_FULL}"},
        {"tag": "component", "value": "{INVENTORY.NAME}"}
    ]
}"""


def setup_action(zapi, mediatype_id):
    """
    Configura uma ação no Zabbix para usar o tipo de mídia.
    
    Args:
        zapi: Objeto ZabbixAPI conectado
        mediatype_id: ID do tipo de mídia criado
    """
    try:
        # Verificar se a ação já existe
        existing = zapi.action.get(filter={"name": "Enviar alertas para Dorothy"})
        if existing:
            print("Ação 'Enviar alertas para Dorothy' já existe.")
            return
        
        # Criar a ação
        action = {
            "name": "Enviar alertas para Dorothy",
            "eventsource": 0,  # triggers
            "status": 0,  # enabled
            "filter": {
                "evaltype": 0,  # and/or
                "conditions": [
                    {
                        "conditiontype": 16,  # maintenance status
                        "operator": 7,  # not in
                        "value": ""
                    },
                    {
                        "conditiontype": 5,  # trigger severity
                        "operator": 5,  # >=
                        "value": "3"  # 3 = warning (0-not classified, 1-info, 2-warning, etc.)
                    }
                ]
            },
            "operations": [
                {
                    "operationtype": 0,  # send message
                    "esc_step_from": 1,
                    "esc_step_to": 1,
                    "esc_period": "0",
                    "opmessage": {
                        "default_msg": 1,
                        "mediatypeid": str(mediatype_id)
                    },
                    "opmessage_usr": [
                        {
                            "userid": "1"  # Usuário Admin por padrão
                        }
                    ]
                }
            ],
            "recovery_operations": [
                {
                    "operationtype": 0,  # send message
                    "opmessage": {
                        "default_msg": 1,
                        "mediatypeid": str(mediatype_id)
                    },
                    "opmessage_usr": [
                        {
                            "userid": "1"  # Usuário Admin por padrão
                        }
                    ]
                }
            ]
        }
        
        result = zapi.action.create(**action)
        print("Ação 'Enviar alertas para Dorothy' criada com sucesso!")
        
    except Exception as e:
        print(f"Erro ao configurar ação: {str(e)}")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Configura o Zabbix para enviar alertas para a API Dorothy'
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
    parser.add_argument(
        '--api-url',
        default='http://dorothy-api:8000',
        help='URL da API Dorothy (padrão: http://dorothy-api:8000)'
    )
    
    args = parser.parse_args()
    
    # Aguardar um tempo para garantir que o Zabbix esteja pronto
    wait_for_zabbix(args.zabbix_url)
    
    # Configurar o tipo de mídia
    setup_media_type(
        args.zabbix_url,
        args.username,
        args.password,
        args.api_url
    )


def wait_for_zabbix(zabbix_url, max_retries=30, retry_interval=5):
    """
    Aguarda até que a API do Zabbix esteja disponível.
    
    Args:
        zabbix_url: URL da API do Zabbix
        max_retries: Número máximo de tentativas
        retry_interval: Intervalo entre tentativas em segundos
    """
    print(f"Aguardando o Zabbix estar disponível em {zabbix_url}...")
    
    for i in range(max_retries):
        try:
            # Tentar acessar a API
            response = requests.get(
                zabbix_url.replace('api_jsonrpc.php', ''),
                verify=False,
                timeout=5
            )
            if response.status_code == 200:
                print("Zabbix está disponível! Continuando...")
                time.sleep(5)  # Aguarda mais um pouco para garantir
                return True
        except Exception:
            pass
        
        print(f"Tentativa {i+1}/{max_retries} - Zabbix ainda não disponível.")
        time.sleep(retry_interval)
    
    print("Erro: Zabbix não ficou disponível no tempo esperado.")
    sys.exit(1)


if __name__ == "__main__":
    main()