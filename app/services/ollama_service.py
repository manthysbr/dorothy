import httpx
import json
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.logging import logger, log_erro_integracao


class OllamaService:
    """
    Serviço para interação com a API do Ollama.
    
    Fornece métodos para enviar prompts ao modelo de IA local
    e interpretar suas respostas para tomada de decisões.
    """
    
    def __init__(self):
        """
        Inicializa o serviço com as configurações do Ollama.
        """
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    async def check_connection(self) -> Dict[str, Any]:
        """
        Verifica se a conexão com o Ollama está funcionando.
        
        Returns:
            Dicionário com status e mensagem
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/version",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "name": "ollama",
                        "status": "operational",
                        "version": data.get("version", "unknown"),
                        "message": "Conexão com Ollama estabelecida"
                    }
                else:
                    raise Exception(
                        f"Erro HTTP {response.status_code}: {response.text}"
                    )
                    
        except Exception as e:
            log_erro_integracao("Ollama", "check_connection", e)
            return {
                "name": "ollama",
                "status": "error",
                "message": f"Falha na conexão: {str(e)}"
            }
    
    async def analyze_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa um alerta usando o modelo do Ollama.
        
        Args:
            alert_data: Dados do alerta do Zabbix
            
        Returns:
            Dicionário com a análise e ação recomendada
        """
        # Criamos um prompt que explica claramente a tarefa para o modelo
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(alert_data)
        
        try:
            async with httpx.AsyncClient() as client:
                # Para o deepseek-r1:14b, usamos a API de chat
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "stream": False,
                        "temperature": 0.1,  # Temperatura baixa para respostas mais determinísticas
                        "top_p": 0.9
                    },
                    timeout=60.0  # Aumento do timeout para modelos maiores
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Para a API de chat, o formato da resposta é diferente
                    response_text = result.get("message", {}).get("content", "")
                    analysis = self._parse_ollama_response(response_text)
                    
                    # Log da análise para depuração
                    logger.debug(
                        f"Análise do alerta para host {alert_data.get('host')}: "
                        f"{json.dumps(analysis)}"
                    )
                    
                    return analysis
                else:
                    # Em caso de falha, retornamos uma resposta padrão
                    error_msg = f"Falha ao consultar Ollama: {response.text}"
                    logger.error(error_msg)
                    return {
                        "action": "notify",
                        "confidence": 0.0,
                        "reason": error_msg,
                        "requires_action": False
                    }
        
        except Exception as e:
            error_msg = f"Erro ao processar com Ollama: {str(e)}"
            logger.exception(error_msg)
            return {
                "action": "notify",
                "confidence": 0.0,
                "reason": error_msg,
                "requires_action": False
            }
    
    def _create_system_prompt(self) -> str:
        """
        Cria um prompt de sistema para o modelo.
        
        Returns:
            Prompt de sistema formatado
        """
        return """
        Você é um sistema especializado na análise de alertas do Zabbix e na 
        automação de respostas a incidentes. Sua tarefa é analisar alertas e
        determinar a ação mais adequada baseada nas informações fornecidas.
        
        Você deve responder APENAS com um JSON válido, seguindo exatamente o
        formato solicitado, sem explicações adicionais.
        """
    
    def _create_user_prompt(self, alert_data: Dict[str, Any]) -> str:
        """
        Cria um prompt de usuário estruturado para o modelo.
        
        Args:
            alert_data: Dados do alerta
            
        Returns:
            Prompt formatado
        """
        # Extrair dados relevantes do alerta
        host = alert_data.get('host', 'desconhecido')
        problem = alert_data.get('problem', 'Sem descrição')
        severity = alert_data.get('severity', 'desconhecida')
        status = alert_data.get('status', 'PROBLEM')
        details = json.dumps(alert_data.get('details', {}), indent=2)
        tags = json.dumps(alert_data.get('tags', []), indent=2)
        
        # Prompt formatado com todas as informações relevantes
        return f"""
        Analise o seguinte alerta do Zabbix e determine a ação mais adequada:

        Host: {host}
        Problema: {problem}
        Severidade: {severity}
        Status: {status}
        
        Detalhes adicionais:
        {details}
        
        Tags:
        {tags}
        
        Possíveis ações:
        1. cleanup-disk: Para problemas de disco cheio
        2. restart-service: Para serviços parados
        3. analyze-processes: Para alta utilização de CPU
        4. restart-application: Para vazamentos de memória
        5. notify: Caso nenhuma ação automática seja apropriada
        
        Responda APENAS com um JSON no seguinte formato:
        {{
          "action": "[nome da ação]",
          "confidence": [valor de 0 a 1],
          "reason": "[motivo da escolha]",
          "requires_action": true/false,
          "recommended_job_id": "[job_id]",
          "job_parameters": {{
            "param1": "valor1",
            "param2": "valor2"
          }}
        }}
        """
    
    def _parse_ollama_response(self, response_text: str) -> Dict[str, Any]:
        """
        Analisa a resposta do Ollama e extrai as informações necessárias.
        
        Args:
            response_text: Texto da resposta do Ollama
            
        Returns:
            Dicionário com os dados extraídos
        """
        try:
            # Tenta extrair JSON do texto de resposta
            # Procura por chaves que indicam o início e fim de um JSON
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            
            if start_idx >= 0 and end_idx > 0:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Garantir que campos obrigatórios existem
                if "action" not in result:
                    result["action"] = "notify"
                if "confidence" not in result:
                    result["confidence"] = 0.5
                if "requires_action" not in result:
                    result["requires_action"] = False
                    
                return result
            
            # Se não conseguir extrair um JSON válido, retorna resposta padrão
            return {
                "action": "notify",
                "confidence": 0.5,
                "reason": "Não foi possível determinar ação automática.",
                "requires_action": False
            }
            
        except json.JSONDecodeError as e:
            # Em caso de falha na decodificação do JSON
            logger.error(f"Erro ao decodificar resposta JSON: {str(e)}")
            logger.debug(f"Resposta original: {response_text}")
            return {
                "action": "notify",
                "confidence": 0.0,
                "reason": "Falha ao interpretar resposta do modelo.",
                "requires_action": False
            }