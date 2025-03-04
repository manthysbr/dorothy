from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

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