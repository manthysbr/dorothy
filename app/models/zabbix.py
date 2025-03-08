from pydantic import BaseModel, Field, root_validator
from typing import Optional, Dict, Any, List, Union
import time

class ZabbixTrigger(BaseModel):
    """
    Modelo representando o gatilho de um alerta do Zabbix.
    """
    id: str
    name: str
    severity: str
    status: str
    hostname: str
    ip: Optional[str] = None


class ZabbixAlert(BaseModel):
    """
    Modelo de dados para alertas recebidos do Zabbix.
    
    Baseado na estrutura de alertas padrão do Zabbix quando configurado
    para enviar webhooks.
    """
    event_id: str = Field(..., description="ID do evento no Zabbix")
    host: str = Field(..., description="Nome do host que gerou o alerta")
    problem: str = Field(..., description="Descrição do problema")
    severity: str = Field(..., description="Nível de severidade do alerta")
    timestamp: Optional[int] = Field(None, description="Timestamp do evento")
    item_id: Optional[str] = Field(None, description="ID do item no Zabbix")
    trigger_id: Optional[str] = Field(None, description="ID do trigger no Zabbix")
    status: Optional[str] = Field(None, description="Status do problema (PROBLEM/RESOLVED)")
    
    # Campos opcionais para informações adicionais
    details: Optional[Dict[str, Any]] = Field(
        default={}, 
        description="Detalhes adicionais do alerta"
    )
    tags: Optional[List[Dict[str, str]]] = Field(
        default=[], 
        description="Tags associadas ao evento"
    )
    
    @root_validator(pre=True)
    def extract_nested_fields(cls, values):
        """
        Validador para manipular diferentes formatos de webhook do Zabbix.
        
        Este validador trata:
        1. Dados enviados diretamente no formato esperado
        2. Dados encapsulados em uma chave Message
        3. Dados enviados em outros formatos comuns do Zabbix
        
        Args:
            values: Valores recebidos na requisição
            
        Returns:
            Dicionário com valores normalizados
        """
        # Captura o payload raw para debug
        import json
        from app.core.logging import logger
        logger.debug(f"Valores recebidos no ZabbixAlert: {json.dumps(values)[:200]}...")
        
        # Caso 1: Se os dados vierem em um campo 'Message'
        if 'Message' in values and values['Message']:
            try:
                # Tenta parsear o campo Message como JSON
                message_data = json.loads(values['Message'])
                if isinstance(message_data, dict):
                    # Usa os dados do campo Message
                    values.update(message_data)
            except (json.JSONDecodeError, TypeError):
                # Se Message não for JSON válido, tenta usar como problem
                if 'problem' not in values:
                    values['problem'] = values['Message']
        
        # Caso 2: Se os dados vierem em um campo 'Subject' e faltar o 'problem'
        if 'problem' not in values and 'Subject' in values and values['Subject']:
            values['problem'] = values['Subject']
        
        # Caso 3: Extrai os campos do objeto details, se presente
        if 'details' in values and isinstance(values['details'], dict):
            details = values['details']
            
            # Extrai campos do details para o nível principal se necessário
            for field in ['item_id', 'trigger_id']:
                if field in details and field not in values:
                    values[field] = details[field]
            
            # Se não houver problem/severity, tenta extrair do details
            if 'problem' not in values and 'description' in details:
                values['problem'] = details['description']
            if 'severity' not in values and 'priority' in details:
                values['severity'] = details['priority']
        
        # Garante campos obrigatórios com valores padrão
        if 'event_id' not in values:
            values['event_id'] = values.get('eventid') or values.get('id') or str(int(time.time()))
        if 'host' not in values:
            values['host'] = values.get('hostname') or values.get('host_name') or 'unknown-host'
        if 'problem' not in values:
            values['problem'] = values.get('name') or values.get('description') or 'Unknown problem'
        if 'severity' not in values:
            values['severity'] = values.get('priority') or 'not classified'
        
        # Remove campos não utilizados
        if 'endpoint' in values:
            values.pop('endpoint')
        if 'URL' in values:
            values.pop('URL')
        
        return values