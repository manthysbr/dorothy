from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
import time
import json

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

@router.post("/alert/raw", summary="Captura o payload bruto do webhook do Zabbix")
async def capture_raw_payload(request: Request) -> Dict[str, Any]:
    """
    Endpoint para capturar o payload bruto enviado pelo webhook do Zabbix.
    
    Este endpoint é usado apenas para depuração e diagnóstico.
    
    Args:
        request: Requisição HTTP contendo o payload bruto
        
    Returns:
        O payload recebido e informações de diagnóstico
    """
    try:
        # Captura o corpo bruto da requisição
        payload = await request.body()
        payload_str = payload.decode("utf-8")
        
        # Registra o payload recebido para análise
        logger.info(f"Payload webhook raw recebido: {payload_str[:200]}...")
        
        # Tenta parsear como JSON
        try:
            json_payload = json.loads(payload_str)
            is_valid_json = True
            
            # Se for um formulário Zabbix, tenta extrair valor de Message
            message_value = None
            if isinstance(json_payload, dict):
                if "Message" in json_payload:
                    try:
                        message_value = json.loads(json_payload["Message"])
                        logger.info(f"Mensagem extraída: {message_value}")
                    except:
                        message_value = json_payload["Message"]
        except json.JSONDecodeError:
            json_payload = {"raw_text": payload_str}
            is_valid_json = False
            message_value = None
        
        # Retorna informações de diagnóstico
        return {
            "received_at": int(time.time()),
            "content_type": request.headers.get("content-type", "unknown"),
            "content_length": len(payload_str),
            "is_valid_json": is_valid_json,
            "payload": json_payload,
            "message_extracted": message_value,
            "headers": dict(request.headers)
        }
        
    except Exception as e:
        logger.exception(f"Erro ao capturar payload raw: {str(e)}")
        return {
            "error": str(e),
            "message": "Ocorreu um erro ao processar o payload bruto"
        }
    
@router.post("/alert/direct", summary="Recebe alertas do Zabbix em formato bruto")
async def receive_raw_alert(
    request: Request,
    ollama_service: OllamaService = Depends(lambda: OllamaService()),
    rundeck_service: RundeckService = Depends(lambda: RundeckService())
) -> Dict[str, Any]:
    """
    Endpoint para receber alertas do Zabbix em formato bruto.
    
    Este endpoint é projetado para lidar com o formato enviado diretamente
    pelo webhook do Zabbix, sem a validação do modelo Pydantic.
    
    Args:
        request: Requisição HTTP contendo o payload bruto
        ollama_service: Serviço de conexão com o Ollama (injetado)
        rundeck_service: Serviço de conexão com o Rundeck (injetado)
    
    Returns:
        Detalhes da análise e da ação recomendada
    """
    try:
        # Captura o corpo bruto da requisição
        body = await request.body()
        body_str = body.decode("utf-8")
        
        # Tenta parsear o JSON
        try:
            data = json.loads(body_str)
            logger.info(f"Payload recebido: {body_str[:200]}...")
        except json.JSONDecodeError:
            logger.error(f"Payload inválido (não é JSON): {body_str[:200]}")
            raise HTTPException(
                status_code=400,
                detail="Payload inválido: não é um JSON válido"
            )
        
        # Extrai dados do campo Message se presente
        if "Message" in data:
            try:
                message_content = data["Message"]
                # Tenta parsear o campo Message como JSON
                if isinstance(message_content, str):
                    try:
                        message_data = json.loads(message_content)
                        if isinstance(message_data, dict):
                            logger.info("Dados extraídos do campo Message")
                            data = message_data
                    except json.JSONDecodeError:
                        # Se não for um JSON válido, usa o texto como problem
                        logger.warning("Campo Message não é um JSON válido")
                        data["problem"] = message_content
            except Exception as e:
                logger.error(f"Erro ao processar campo Message: {str(e)}")
        
        # Normaliza os dados para garantir campos obrigatórios
        alert_data = {
            "event_id": data.get("event_id") or data.get("eventid") or str(int(time.time())),
            "host": data.get("host") or data.get("hostname") or "unknown-host",
            "problem": data.get("problem") or data.get("subject") or data.get("description") or "Unknown problem",
            "severity": data.get("severity") or "not classified",
            "status": data.get("status") or "PROBLEM",
            "timestamp": data.get("timestamp") or int(time.time())
        }
        
        # Adiciona campos opcionais se presentes
        if "details" in data and isinstance(data["details"], dict):
            alert_data["details"] = data["details"]
        else:
            alert_data["details"] = {}
            
        if "tags" in data and isinstance(data["tags"], list):
            alert_data["tags"] = data["tags"]
        else:
            alert_data["tags"] = []
            
        # Envia para análise do Ollama
        analysis_result = await ollama_service.analyze_alert(alert_data)
        
        # Se a análise indicar necessidade de ação no Rundeck
        action_response = {}
        if analysis_result.get("requires_action", False):
            job_id = analysis_result.get("recommended_job_id")
            if job_id:
                action_response = await rundeck_service.execute_job(
                    job_id=job_id, 
                    parameters=analysis_result.get("job_parameters", {})
                )
                
        # Monta a resposta
        response = {
            "event_id": alert_data["event_id"],
            "host": alert_data["host"],
            "problem": alert_data["problem"],
            "severity": alert_data["severity"],
            "analysis": analysis_result,
            "action_taken": action_response
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao processar alerta bruto: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar alerta: {str(e)}"
        )