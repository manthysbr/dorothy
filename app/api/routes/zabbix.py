from fastapi import APIRouter, Depends, HTTPException
from app.models.zabbix import ZabbixAlert
from app.services.ollama_service import OllamaService
from app.services.rundeck_service import RundeckService
from typing import Dict, Any

router = APIRouter()

@router.post("/alert", summary="Recebe alertas do Zabbix")
async def receive_alert(
    alert: ZabbixAlert,
    ollama_service: OllamaService = Depends(lambda: OllamaService()),
    rundeck_service: RundeckService = Depends(lambda: RundeckService())
) -> Dict[str, Any]:
    """
    Endpoint para receber alertas do Zabbix.
    
    Processa o alerta usando o serviço Ollama e determina a ação apropriada.
    
    Args:
        alert: Dados do alerta do Zabbix
        ollama_service: Serviço de conexão com o Ollama (injetado)
        rundeck_service: Serviço de conexão com o Rundeck (injetado)
    
    Returns:
        Detalhes da análise e da ação recomendada
    """
    try:
        # Converte o modelo Pydantic para dicionário
        alert_dict = alert.model_dump()
        
        # Envia para análise do Ollama
        analysis_result = await ollama_service.analyze_alert(alert_dict)
        
        # Se a análise indicar necessidade de ação no Rundeck
        action_response = {}
        if analysis_result.get("requires_action", False):
            job_id = analysis_result.get("recommended_job_id")
            if job_id:
                action_response = await rundeck_service.execute_job(
                    job_id=job_id, 
                    parameters=analysis_result.get("job_parameters", {})
                )
        
        # Adiciona informações adicionais na resposta
        response = {
            "event_id": alert.event_id,
            "host": alert.host,
            "problem": alert.problem,
            "severity": alert.severity,
            "analysis": analysis_result,
            "action_taken": action_response
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar alerta: {str(e)}"
        )