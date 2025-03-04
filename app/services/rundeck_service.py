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
    
    async def execute_job(
        self,
        job_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executa um job no Rundeck.
        
        Args:
            job_id: ID do job a ser executado
            parameters: Parâmetros para a execução do job
            
        Returns:
            Resposta do Rundeck
        """
        if not job_id:
            return {
                "success": False,
                "message": "ID do job não especificado"
            }
            
        # Se job_id for uma string de ação, obter o ID real do mapeamento
        if job_id in self.action_mapping:
            job_id = self.action_mapping[job_id].get("job_id", "")
            if not job_id:
                return {
                    "success": False,
                    "message": f"ID do job para ação '{job_id}' não configurado"
                }
        
        parameters = parameters or {}
        
        try:
            async with httpx.AsyncClient() as client:
                # Endpoint para executar um job
                url = f"{self.api_url}/job/{job_id}/run"
                
                # Payload com os parâmetros do job
                payload = {
                    "argString": self._format_parameters(parameters)
                }
                
                # Executar o job
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code in (200, 201):
                    execution = response.json()
                    logger.info(
                        f"Job executado com sucesso. ID: {execution.get('id')}"
                    )
                    return {
                        "success": True,
                        "execution_id": execution.get("id"),
                        "job_id": job_id,
                        "status": execution.get("status")
                    }
                else:
                    error_msg = (
                        f"Erro ao executar job. Status: {response.status_code}, "
                        f"Resposta: {response.text}"
                    )
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "message": error_msg,
                        "job_id": job_id,
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            error_msg = f"Exceção ao executar job: {str(e)}"
            log_erro_integracao("Rundeck", "execute_job", e)
            return {
                "success": False,
                "message": error_msg,
                "job_id": job_id
            }
    
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