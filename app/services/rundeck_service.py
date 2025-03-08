import httpx
import json
import uuid
import time
from typing import Dict, Any, Optional, Tuple

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
        self.base_url = self.api_url.rsplit('/api', 1)[0]
        
        # Headers padrão para todas as requisições
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Rundeck-Auth-Token": self.token
        }

        # Mapeamento de jobs para webhooks
        self._webhook_map = {
            # Com underscore (formato do function calling)
            "cleanup_disk": "CjErsoegWTqAkBT0W54n3bTNg7iIsy4I#limpeza_de_disco",
            "restart_service": "fHhzLf806fPUOiCpdhCBM7hR5zzI8B5J#restart_servico",
            "analyze_processes": "n4aedKfdHKziD46ayYWMG0I7NHTnM9Gt#analise",
            "restart_application": "a8UhsPtDe73LrMWczcoXk5b7PYwFjyD6#restart_app",
            "notify": "2836bJRcdX4MYF9hTqCcH0yaLsAGZaXA#notificar",
            
            # Com hífen (formato das variáveis de ambiente)
            "cleanup-disk": "CjErsoegWTqAkBT0W54n3bTNg7iIsy4I#limpeza_de_disco",
            "restart-service": "fHhzLf806fPUOiCpdhCBM7hR5zzI8B5J#restart_servico",
            "analyze-processes": "n4aedKfdHKziD46ayYWMG0I7NHTnM9Gt#analise",
            "restart-app": "a8UhsPtDe73LrMWczcoXk5b7PYwFjyD6#restart_app",
            "notify": "2836bJRcdX4MYF9hTqCcH0yaLsAGZaXA#notificar"
        }

    def _get_webhook_url(self, job_id: str) -> Tuple[Optional[str], str]:
        """
        Obtém a URL do webhook para um determinado job_id.
        
        Args:
            job_id: Identificador do job
            
        Returns:
            Tupla com (URL do webhook ou None se não encontrado, mensagem de status)
        """
        # Tenta diferentes formatos do job_id
        variants = [
            job_id,                      # Original
            job_id.replace('-', '_'),    # Converte hífen para underscore
            job_id.replace('_', '-')     # Converte underscore para hífen
        ]
        
        # Registra tentativas para debugging
        logger.debug(f"Buscando webhook para job '{job_id}', tentando variantes: {variants}")
        
        # Busca nas variantes
        for variant in variants:
            if variant in self._webhook_map:
                webhook_id = self._webhook_map[variant]
                logger.debug(f"Webhook encontrado para variante '{variant}': {webhook_id}")
                return f"{self.base_url}/api/45/webhook/{webhook_id}", "ok"
        
        # Se não encontrou, registra o problema
        logger.warning(
            f"Job ID '{job_id}' não encontrado no mapeamento de webhooks. "
            f"Tentativas: {variants}"
        )
        return None, f"Job ID desconhecido: {job_id}"

    async def execute_job(self, job_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa um job no Rundeck usando webhook.
        
        Args:
            job_id: ID do job para executar
            parameters: Parâmetros para o job
            
        Returns:
            Resultado da chamada
        """
        logger.info(f"Iniciando execução do job: {job_id} com parâmetros: {parameters}")
        
        # Obtém URL do webhook
        webhook_url, status = self._get_webhook_url(job_id)
        
        # Se não encontrou webhook, tenta fallback
        if webhook_url is None:
            logger.warning(f"Webhook não encontrado para job {job_id}, tentando fallback")
            
            # Tenta usar mapeamentos alternativos diretos
            fallback_map = {
                "cleanup-disk": "CjErsoegWTqAkBT0W54n3bTNg7iIsy4I#limpeza_de_disco",
                "restart-service": "fHhzLf806fPUOiCpdhCBM7hR5zzI8B5J#restart_servico",
                "analyze-processes": "n4aedKfdHKziD46ayYWMG0I7NHTnM9Gt#analise",
                "restart-app": "a8UhsPtDe73LrMWczcoXk5b7PYwFjyD6#restart_app",
                "notify": "2836bJRcdX4MYF9hTqCcH0yaLsAGZaXA#notificar"
            }
            
            if job_id in fallback_map:
                webhook_id = fallback_map[job_id]
                logger.info(f"Usando webhook alternativo para {job_id}: {webhook_id}")
                webhook_url = f"{self.base_url}/api/45/webhook/{webhook_id}"
            else:
                # Último recurso: verifica se o job_id é exatamente o webhook ID
                for webhook_id in self._webhook_map.values():
                    if job_id in webhook_id:
                        logger.info(f"Usando job_id diretamente como webhook: {webhook_id}")
                        webhook_url = f"{self.base_url}/api/45/webhook/{webhook_id}"
                        break
        
        # Se ainda não encontrou, retorna erro
        if webhook_url is None:
            logger.error(f"Não foi possível encontrar webhook para job: {job_id}")
            return {
                "error": "Job ID desconhecido",
                "job_id": job_id,
                "status": "failed"
            }
        
        # Adicionar ID do alerta e timestamp para rastreabilidade
        parameters["alert_id"] = str(uuid.uuid4())
        parameters["timestamp"] = int(time.time())
        
        try:
            # Se estamos em modo simulação (sem token válido), logamos apenas
            if not self.token or self.token == "admin12345":
                logger.info(
                    f"SIMULAÇÃO: Job {job_id} executaria com URL {webhook_url} e "
                    f"parâmetros: {json.dumps(parameters, indent=2)}"
                )
                return {
                    "job_id": job_id,
                    "parameters": parameters,
                    "status": "simulated",
                    "webhook_url": webhook_url,
                    "message": "Job simulado (token não configurado)"
                }
                
            # Caso contrário, fazemos a chamada real
            async with httpx.AsyncClient() as client:
                logger.info(f"Acionando webhook: {webhook_url}")
                response = await client.post(
                    webhook_url, 
                    json=parameters,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                logger.info(
                    f"Job {job_id} executado com sucesso através do webhook. "
                    f"Status: {response.status_code}"
                )
                return {
                    "job_id": job_id,
                    "parameters": parameters,
                    "status": "triggered",
                    "webhook_url": webhook_url,
                    "response_status": response.status_code,
                    "webhook_response": response.json() if response.text else {}
                }
        except Exception as e:
            log_erro_integracao("Rundeck", "execute_job", e)
            logger.error(
                f"Erro ao executar job {job_id} via webhook {webhook_url}: {str(e)}"
            )
            return {
                "error": f"Falha ao executar job: {str(e)}",
                "job_id": job_id,
                "webhook_url": webhook_url,
                "status": "error"
            }