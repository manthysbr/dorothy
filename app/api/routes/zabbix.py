from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import time

from app.models.zabbix import ZabbixAlert
from app.services.ollama_service import OllamaService
from app.services.rundeck_service import RundeckService
from app.core.logging import logger  

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

@router.post("/alert/debug", summary="Versão de depuração do endpoint de alertas")
async def debug_alert(
    alert: ZabbixAlert,
    ollama_service: OllamaService = Depends(lambda: OllamaService()),
    rundeck_service: RundeckService = Depends(lambda: RundeckService())
) -> Dict[str, Any]:
    """
    Versão de depuração do endpoint de alertas que retorna informações detalhadas.
    
    Processa o alerta e retorna informações adicionais para depuração.
    
    Args:
        alert: Dados do alerta do Zabbix
        ollama_service: Serviço para processar com o LLM
        rundeck_service: Serviço para executar jobs
        
    Returns:
        Informações detalhadas sobre o processamento
    """
    try:
        start_time = time.time()
        
        # Registra informações do alerta
        logger.info(f"[DEBUG] Recebido alerta de {alert.host}: {alert.problem}")
        
        # Converte o modelo Pydantic para dicionário
        alert_dict = alert.model_dump()
        
        # Envia para análise do Ollama e mede o tempo
        ollama_start = time.time()
        analysis_result = await ollama_service.analyze_alert(alert_dict)
        ollama_time = time.time() - ollama_start
        
        # Simula a execução no Rundeck mas não executa realmente
        rundeck_result = None
        if analysis_result.get("requires_action", False):
            job_id = analysis_result.get("recommended_job_id")
            if job_id:
                rundeck_result = {
                    "would_execute": {
                        "job_id": job_id,
                        "parameters": analysis_result.get("job_parameters", {})
                    }
                }
        
        # Calcula tempo total
        total_time = time.time() - start_time
        
        # Retorna resposta detalhada
        return {
            "event_id": alert.event_id,
            "host": alert.host,
            "problem": alert.problem,
            "severity": alert.severity,
            "processing_details": {
                "ollama_model": ollama_service.model,
                "ollama_time_seconds": round(ollama_time, 2),
                "total_time_seconds": round(total_time, 2)
            },
            "analysis": analysis_result,
            "rundeck_simulation": rundeck_result,
            "timestamp": int(time.time()),
            "note": "Este é um endpoint de debug que não executa ações reais no Rundeck"
        }
    
    except Exception as e:
        logger.exception(f"[DEBUG] Erro no processamento: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar alerta (DEBUG): {str(e)}"
        )