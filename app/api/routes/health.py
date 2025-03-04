from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
import time
import platform

from app.services.ollama_service import OllamaService
from app.services.rundeck_service import RundeckService
from app.core.logging import logger
from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="Verifica o status básico da API")
async def health_check() -> Dict[str, Any]:
    """
    Retorna informações básicas sobre o status da API.
    
    Este é um endpoint rápido para verificações simples de disponibilidade.
    Não faz verificações em serviços externos.
    
    Returns:
        Status basic da aplicação
    """
    return {
        "status": "online",
        "version": settings.API_VERSION,
        "timestamp": int(time.time())
    }


@router.get(
    "/health/detailed", 
    summary="Verifica o status detalhado da API e suas dependências"
)
async def detailed_health(
    ollama_service: OllamaService = Depends(lambda: OllamaService()),
    rundeck_service: RundeckService = Depends(lambda: RundeckService())
) -> Dict[str, Any]:
    """
    Realiza uma verificação completa do sistema e seus componentes.
    
    Verifica a conexão com serviços externos (Ollama e Rundeck)
    e fornece informações de sistema.
    
    Args:
        ollama_service: Serviço para verificar conexão com Ollama
        rundeck_service: Serviço para verificar conexão com Rundeck
        
    Returns:
        Relatório detalhado do status de todos os componentes
    """
    start_time = time.time()
    
    # Informações do sistema
    system_info = {
        "python_version": platform.python_version(),
        "system": platform.system(),
        "platform": platform.platform()
    }
    
    # Verificar serviços externos
    services_status = await _check_services(ollama_service, rundeck_service)
    
    # Status dos componentes
    components = [
        {
            "name": "api",
            "status": "operational",
            "message": "API está funcionando normalmente"
        },
        *services_status
    ]
    
    # Calcular o tempo de resposta
    response_time = time.time() - start_time
    
    return {
        "status": "operational",
        "version": settings.API_VERSION,
        "components": components,
        "system_info": system_info,
        "response_time_ms": round(response_time * 1000, 2),
        "timestamp": int(time.time())
    }


async def _check_services(
    ollama_service: OllamaService,
    rundeck_service: RundeckService
) -> List[Dict[str, Any]]:
    """
    Verifica o status dos serviços externos.
    
    Args:
        ollama_service: Serviço Ollama
        rundeck_service: Serviço Rundeck
        
    Returns:
        Lista de status dos serviços
    """
    services_status = []
    
    # Verificar Ollama
    try:
        ollama_status = await ollama_service.check_connection()
    except Exception as e:
        logger.error(f"Falha na verificação do Ollama: {str(e)}")
        ollama_status = {
            "name": "ollama",
            "status": "error",
            "message": f"Falha na conexão: {str(e)}"
        }
    
    services_status.append(ollama_status)
    
    # Verificar Rundeck
    try:
        rundeck_status = await rundeck_service.check_connection()
    except Exception as e:
        logger.error(f"Falha na verificação do Rundeck: {str(e)}")
        rundeck_status = {
            "name": "rundeck",
            "status": "error",
            "message": f"Falha na conexão: {str(e)}"
        }
    
    services_status.append(rundeck_status)
    
    return services_status