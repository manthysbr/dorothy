import os
from typing import Dict, Any

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configurações da aplicação, carregadas de variáveis de ambiente.
    
    Para desenvolvimento, use um arquivo .env na raiz do projeto.
    Para produção, configure as variáveis de ambiente no sistema.
    """
    # API configurações
    API_TITLE: str = "Dorothy - API de automação de alertas"
    API_DESCRIPTION: str = "API para automação de alertas do Zabbix usando LLMs"
    API_VERSION: str = "0.1.0"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    # Ollama configurações
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL", 
        "http://localhost:11434"
    )
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    
    # Rundeck configurações
    RUNDECK_API_URL: str = os.getenv(
        "RUNDECK_API_URL", 
        "http://localhost:4440/api/41"
    )
    RUNDECK_TOKEN: str = os.getenv("RUNDECK_TOKEN", "")
    RUNDECK_PROJECT: str = os.getenv("RUNDECK_PROJECT", "dorothy")
    
    # Mapeamento de ações para jobs do Rundeck
    ACTION_MAPPING: Dict[str, Dict[str, Any]] = {
        "cleanup-disk": {
            "job_id": os.getenv("RUNDECK_JOB_CLEANUP_DISK", ""),
            "description": "Limpa espaço em disco"
        },
        "restart-service": {
            "job_id": os.getenv("RUNDECK_JOB_RESTART_SERVICE", ""),
            "description": "Reinicia um serviço parado"
        },
        "analyze-processes": {
            "job_id": os.getenv("RUNDECK_JOB_ANALYZE_PROCESSES", ""),
            "description": "Analisa processos consumindo muita CPU"
        },
        "restart-application": {
            "job_id": os.getenv("RUNDECK_JOB_RESTART_APPLICATION", ""),
            "description": "Reinicia uma aplicação com vazamento de memória"
        },
        "notify": {
            "job_id": os.getenv("RUNDECK_JOB_NOTIFY", ""),
            "description": "Envia notificação para equipe"
        }
    }


# Instância global de configurações
settings = Settings()