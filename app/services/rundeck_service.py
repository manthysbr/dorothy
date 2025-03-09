import httpx
import json
import uuid
import time
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.logging import logger, log_erro_integracao


class RundeckService:
    """
    Serviço para interação com a API do Rundeck via webhooks.
    
    Fornece métodos para executar jobs através de webhooks pré-configurados.
    """
    
    def __init__(self):
        """
        Inicializa o serviço com as URLs de webhooks fixas.
        """
        # Define a URL base para os webhooks
        self.base_url = "http://rundeck:4440"  # URL direta para o contêiner do Rundeck
        
        # Mapeamento simples e direto dos jobs para webhooks completos
        self.webhook_urls = {
            "cleanup-disk": f"{self.base_url}/api/45/webhook/CjErsoegWTqAkBT0W54n3bTNg7iIsy4I#limpeza_de_disco",
            "restart-service": f"{self.base_url}/api/45/webhook/fHhzLf806fPUOiCpdhCBM7hR5zzI8B5J#restart_servico",
            "analyze-processes": f"{self.base_url}/api/45/webhook/n4aedKfdHKziD46ayYWMG0I7NHTnM9Gt#analise",
            "restart-app": f"{self.base_url}/api/45/webhook/a8UhsPtDe73LrMWczcoXk5b7PYwFjyD6#restart_app",
            "notify": f"{self.base_url}/api/45/webhook/2836bJRcdX4MYF9hTqCcH0yaLsAGZaXA#notificar",
            
            # Também adicione as versões com underscore para compatibilidade
            "cleanup_disk": f"{self.base_url}/api/45/webhook/CjErsoegWTqAkBT0W54n3bTNg7iIsy4I#limpeza_de_disco",
            "restart_service": f"{self.base_url}/api/45/webhook/fHhzLf806fPUOiCpdhCBM7hR5zzI8B5J#restart_servico",
            "analyze_processes": f"{self.base_url}/api/45/webhook/n4aedKfdHKziD46ayYWMG0I7NHTnM9Gt#analise",
            "restart_application": f"{self.base_url}/api/45/webhook/a8UhsPtDe73LrMWczcoXk5b7PYwFjyD6#restart_app",
        }
        
        # Flag para controlar se usamos simulação ou execução real
        # Padrão: False (executa chamadas reais)
        self.simulation_mode = False
        
        # Loga os webhooks disponíveis
        logger.info(f"RundeckService inicializado com {len(self.webhook_urls)} webhooks configurados")
        logger.info(f"Modo de simulação: {'ATIVADO' if self.simulation_mode else 'DESATIVADO'}")

    async def execute_job(self, job_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa um job no Rundeck usando webhook direto.
        
        Args:
            job_id: ID do job para executar
            parameters: Parâmetros para o job
            
        Returns:
            Resultado da chamada
        """
        # Normaliza o job_id (pode vir com _ ou -)
        job_id_normalized = job_id.replace('_', '-')
        
        # Adiciona informações para rastreabilidade
        parameters["alert_id"] = str(uuid.uuid4())
        parameters["timestamp"] = int(time.time())
        
        # Log inicial
        logger.info(f"Iniciando execução do job: {job_id} com parâmetros: {parameters}")
        
        # Obtém a URL do webhook
        webhook_url = self.webhook_urls.get(job_id) or self.webhook_urls.get(job_id_normalized)
        
        # Se não encontrou, usa um webhook padrão com base no tipo de problema
        if not webhook_url:
            logger.warning(f"Webhook não encontrado para job {job_id}, usando fallback")
            
            # Mapeamento de emergência
            if "disk" in job_id.lower():
                webhook_url = self.webhook_urls["cleanup-disk"]
            elif "service" in job_id.lower():
                webhook_url = self.webhook_urls["restart-service"]
            elif "process" in job_id.lower():
                webhook_url = self.webhook_urls["analyze-processes"]
            else:
                webhook_url = self.webhook_urls["notify"]
                
        logger.info(f"Usando webhook: {webhook_url}")
        
        try:
            # Verifica se estamos no modo simulação
            if self.simulation_mode:
                logger.info(
                    f"SIMULAÇÃO: Job {job_id} executaria com URL {webhook_url} e "
                    f"parâmetros: {json.dumps(parameters, indent=2)}"
                )
                
                return {
                    "job_id": job_id,
                    "parameters": parameters,
                    "status": "simulated",
                    "webhook_url": webhook_url,
                    "message": "Job simulado com sucesso"
                }
            
            # Modo de execução real - faz a chamada HTTP ao webhook
            logger.info(f"Executando webhook: {webhook_url}")
            
            async with httpx.AsyncClient() as client:
                # Configurar headers - webhooks não precisam de token
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                # Fazer a chamada HTTP
                response = await client.post(
                    webhook_url,
                    json=parameters,
                    headers=headers,
                    timeout=30.0
                )
                
                # Log da resposta para debug
                logger.debug(f"Resposta do webhook - Status: {response.status_code}")
                if response.text:
                    try:
                        logger.debug(f"Conteúdo da resposta: {json.dumps(response.json(), indent=2)}")
                    except:
                        logger.debug(f"Conteúdo da resposta (texto): {response.text[:500]}")
                
                # Verificar se a chamada foi bem sucedida
                response.raise_for_status()
                
                logger.info(f"Job {job_id} executado com sucesso através do webhook")
                return {
                    "status": "triggered",
                    "job_id": job_id,
                    "webhook_url": webhook_url,
                    "response_status": response.status_code,
                    "message": f"Job executado com sucesso (Status: {response.status_code})"
                }
                
        except Exception as e:
            log_erro_integracao("Rundeck", "execute_job", e)
            logger.error(f"Erro ao executar job {job_id}: {str(e)}")
            return {
                "error": f"Falha ao executar job: {str(e)}",
                "job_id": job_id,
                "status": "error"
            }