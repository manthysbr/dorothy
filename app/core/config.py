import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Settings(BaseModel):
    """
    Configurações da aplicação armazenadas de forma centralizada.
    Utiliza variáveis de ambiente para maior segurança.
    """
    APP_NAME: str = "Dorothy - Automação Inteligente"
    API_V1_STR: str = "/api/v1"
    
    # Configurações do Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    
    # Configurações do Rundeck
    RUNDECK_URL: str = os.getenv("RUNDECK_URL", "")
    RUNDECK_TOKEN: str = os.getenv("RUNDECK_TOKEN", "")
    RUNDECK_PROJECT: str = os.getenv("RUNDECK_PROJECT", "")
    
    # Mapeamento de problemas para jobs do Rundeck
    # Na prática, isso poderia vir de um banco de dados
    ALERT_TO_JOB_MAPPING: dict = {
        "disk_full": "cleanup-disk",
        "service_down": "restart-service",
        "high_cpu": "analyze-processes",
        "memory_leak": "restart-application"
    }

settings = Settings()