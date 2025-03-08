import httpx
import json
from typing import Dict, Any, Optional
from urllib.parse import quote

from app.core.config import settings
from app.core.logging import logger, log_erro_integracao


class RundeckService:
    """
    Serviço para interação com a API do Rundeck.
    
    Fornece métodos para executar jobs e verificar o status do Rundeck.
    """
    
    def __init__(self):
        """
        Inicializa o serviço com as configurações do Rundeck.
        """
        self.api_url = settings.RUNDECK_API_URL
        self.token = settings.RUNDECK_TOKEN
        self.project = settings.RUNDECK_PROJECT
        self.action_mapping = settings.ACTION_MAPPING
        
        # Headers padrão para todas as requisições
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Rundeck-Auth-Token": self.token
        }
    
    async def check_connection(self) -> Dict[str, Any]:
        """
        Verifica se a conexão com o Rundeck está funcionando.
        
        Returns:
            Dicionário com status e mensagem
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/system/info",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "operational",
                        "version": data.get("system", {}).get("version", ""),
                        "message": "Conexão com Rundeck estabelecida"
                    }
                else:
                    raise Exception(
                        f"Erro HTTP {response.status_code}: {response.text}"
                    )
                    
        except Exception as e:
            log_erro_integracao("Rundeck", "check_connection", e)
            return {
                "status": "error",
                "message": f"Falha na conexão: {str(e)}"
            }
    
    async def execute_job(self, job_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa um job no Rundeck usando webhook.
        
        Args:
            job_id: ID do job para executar
            parameters: Parâmetros para o job
            
        Returns:
            Resultado da chamada
        """
        # Mapear job_id para webhook e função
        webhook_map = {
            "cleanup_disk": "CjErsoegWTqAkBT0W54n3bTNg7iIsy4I#limpeza_de_disco",
            "restart_service": "fHhzLf806fPUOiCpdhCBM7hR5zzI8B5J#restart_servico",
            "notify": "2836bJRcdX4MYF9hTqCcH0yaLsAGZaXA#notificar",
            "analyze_processes": "n4aedKfdHKziD46ayYWMG0I7NHTnM9Gt#analise"
        }
        
        if job_id not in webhook_map:
            logger.error(f"Job ID desconhecido: {job_id}")
            return {"error": "Job ID desconhecido"}
        
        webhook = webhook_map[job_id]
        webhook_url = f"{self.base_url}/api/45/webhook/{webhook}"
        
        # Adicionar ID do alerta para rastreabilidade
        parameters["alert_id"] = str(uuid.uuid4())
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=parameters)
                response.raise_for_status()
                
                logger.info(f"Job {job_id} executado com sucesso. Parâmetros: {parameters}")
                return {
                    "job_id": job_id,
                    "parameters": parameters,
                    "status": "triggered",
                    "webhook_response": response.json() if response.text else {}
                }
        except Exception as e:
            logger.error(f"Erro ao executar job {job_id}: {str(e)}")
            return {"error": f"Falha ao executar job: {str(e)}"}
    
    async def get_job_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Verifica o status de execução de um job.
        
        Args:
            execution_id: ID de execução do job
            
        Returns:
            Status da execução
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.api_url}/execution/{execution_id}"
                
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "status": data.get("status"),
                        "started_at": data.get("date-started"),
                        "ended_at": data.get("date-ended"),
                        "job_id": data.get("job", {}).get("id")
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Erro HTTP {response.status_code}",
                        "status": "unknown"
                    }
                    
        except Exception as e:
            log_erro_integracao("Rundeck", "get_job_status", e)
            return {
                "success": False,
                "message": f"Erro ao obter status: {str(e)}",
                "status": "error"
            }
    
    def _format_parameters(self, parameters: Dict[str, Any]) -> str:
        """
        Formata os parâmetros para o formato aceito pelo Rundeck.
        
        Args:
            parameters: Dicionário de parâmetros
            
        Returns:
            String formatada para o Rundeck
        """
        if not parameters:
            return ""
            
        param_strings = []
        for key, value in parameters.items():
            # Para listas, join com vírgulas
            if isinstance(value, list):
                value = ",".join(str(v) for v in value)
            # Codifica valores para URL
            encoded_value = quote(str(value))
            param_strings.append(f"-{key} {encoded_value}")
            
        return " ".join(param_strings)