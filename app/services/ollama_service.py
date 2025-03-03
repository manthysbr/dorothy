import httpx
import json
from typing import Dict, Any, Optional

from app.core.config import settings


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
    
    async def analyze_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa um alerta usando o modelo do Ollama.
        
        Args:
            alert_data: Dados do alerta do Zabbix
            
        Returns:
            Dicionário com a análise e ação recomendada
        """
        # Criamos um prompt que explica claramente a tarefa para o modelo
        prompt = self._create_analysis_prompt(alert_data)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return self._parse_ollama_response(result["response"])
                    
                else:
                    # Em caso de falha, retornamos uma resposta padrão
                    return {
                        "action": "notify",
                        "confidence": 0.0,
                        "reason": f"Falha ao consultar Ollama: {response.text}"
                    }
        
        except Exception as e:
            return {
                "action": "notify",
                "confidence": 0.0,
                "reason": f"Erro ao processar com Ollama: {str(e)}"
            }
    
    def _create_analysis_prompt(self, alert_data: Dict[str, Any]) -> str:
        """
        Cria um prompt estruturado para o modelo do Ollama.
        
        Args:
            alert_data: Dados do alerta
            
        Returns:
            Prompt formatado
        """
        return f"""
        Analise o seguinte alerta do Zabbix e determine a ação mais adequada:

        Host: {alert_data.get('trigger', {}).get('hostname', 'desconhecido')}
        IP: {alert_data.get('trigger', {}).get('ip', 'desconhecido')}
        Severidade: {alert_data.get('trigger', {}).get('severity', 'desconhecida')}
        Problema: {alert_data.get('description', 'Sem descrição')}
        
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
          "reason": "[motivo da escolha]"
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
                return json.loads(json_str)
            
            # Se não conseguir extrair um JSON válido, retorna resposta padrão
            return {
                "action": "notify",
                "confidence": 0.5,
                "reason": "Não foi possível determinar ação automática."
            }
            
        except json.JSONDecodeError:
            # Em caso de falha na decodificação do JSON
            return {
                "action": "notify",
                "confidence": 0.0,
                "reason": "Falha ao interpretar resposta do modelo."
            }