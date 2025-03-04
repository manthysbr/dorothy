import httpx
import json
from typing import Dict, Any, Optional, List

from app.core.config import settings
from app.core.logging import logger, log_erro_integracao


class OllamaService:
    """
    Serviço para interação com a API do Ollama utilizando function calling.
    
    Fornece métodos para enviar prompts ao modelo de IA local e converter
    as respostas em chamadas de funções para automação de ações.
    """
    
    def __init__(self):
        """
        Inicializa o serviço com as configurações do Ollama.
        """
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        
        # Definimos as funções disponíveis e seus schemas
        self.tools = self._create_tools()

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
    
    def _create_tools(self) -> List[Dict[str, Any]]:
        """
        Cria a lista de ferramentas (funções) disponíveis para o LLM.
        
        Returns:
            Lista de definições de ferramentas no formato esperado pelo Ollama
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "cleanup_disk",
                    "description": "Executa limpeza de disco quando há "
                                   "problemas de espaço",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Caminho do sistema de arquivos "
                                               "a ser limpo"
                            },
                            "min_size": {
                                "type": "string",
                                "description": "Tamanho mínimo dos arquivos a "
                                               "limpar (ex: '100MB')"
                            },
                            "file_age": {
                                "type": "string",
                                "description": "Idade mínima dos arquivos a "
                                               "limpar (ex: '7d')"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "restart_service",
                    "description": "Reinicia um serviço que está parado ou "
                                   "instável",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service_name": {
                                "type": "string", 
                                "description": "Nome do serviço a ser "
                                               "reiniciado"
                            },
                            "force": {
                                "type": "boolean",
                                "description": "Se deve forçar a "
                                               "reinicialização"
                            }
                        },
                        "required": ["service_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_processes",
                    "description": "Analisa processos consumindo muitos "
                                   "recursos",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "description": "Tipo de recurso "
                                               "(cpu, memory, io)"
                            },
                            "top_count": {
                                "type": "integer",
                                "description": "Número de processos a listar"
                            }
                        },
                        "required": ["resource_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "restart_application",
                    "description": "Reinicia uma aplicação com problemas de "
                                   "memória",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {
                                "type": "string",
                                "description": "Nome da aplicação"
                            },
                            "graceful": {
                                "type": "boolean",
                                "description": "Se deve aguardar finalização"
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Tempo de espera em segundos"
                            }
                        },
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "notify",
                    "description": "Envia notificação para a equipe técnica",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "team": {
                                "type": "string",
                                "description": "Equipe a ser notificada"
                            },
                            "priority": {
                                "type": "string",
                                "description": "Prioridade da notificação"
                            },
                            "message": {
                                "type": "string",
                                "description": "Mensagem a ser enviada"
                            }
                        },
                        "required": ["message"]
                    }
                }
            }
        ]
    
    async def analyze_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa um alerta usando o modelo do Ollama com function calling.
        
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
                # Configuramos a chamada para usar function calling
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "tools": self.tools,
                        "stream": False,
                        "temperature": 0.1
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Processamos a resposta buscando tool_calls
                    return self._process_ollama_response(result, alert_data)
                else:
                    # Em caso de falha, retornamos uma resposta padrão
                    error_msg = f"Falha ao consultar Ollama: {response.text}"
                    logger.error(error_msg)
                    return self._create_fallback_action(
                        error_msg, 
                        alert_data
                    )
        
        except Exception as e:
            error_msg = f"Erro ao processar com Ollama: {str(e)}"
            logger.exception(error_msg)
            return self._create_fallback_action(
                error_msg, 
                alert_data
            )
    
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
        
        Utilize as funções disponíveis para indicar a ação recomendada, 
        fornecendo os parâmetros corretos.
        
        Não adicione explicações adicionais, apenas chame a função adequada.
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
        Analise o seguinte alerta do Zabbix e determine qual função chamar:

        Host: {host}
        Problema: {problem}
        Severidade: {severity}
        Status: {status}
        
        Detalhes adicionais:
        {details}
        
        Tags:
        {tags}
        
        Com base nessas informações, chame a função mais adequada para 
        resolver o problema. Considere:

        - Para problemas de espaço em disco, use cleanup_disk()
        - Para serviços parados, use restart_service()
        - Para uso elevado de CPU, use analyze_processes()
        - Para problemas de memória, use restart_application()
        - Se não tiver certeza ou nenhuma ação for adequada, use notify()
        """
    
    def _process_ollama_response(
        self, 
        result: Dict[str, Any], 
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Processa a resposta do Ollama, extraindo informações de tool_calls.
        
        Args:
            result: Resposta completa do Ollama
            alert_data: Dados originais do alerta
        
        Returns:
            Dicionário com ação recomendada formatada
        """
        try:
            # Extraímos a mensagem da resposta
            message = result.get("message", {})
            
            # Verificamos se há tool_calls na resposta
            tool_calls = message.get("tool_calls", [])
            
            if not tool_calls:
                logger.warning("Nenhuma ferramenta foi chamada pelo modelo")
                return self._create_fallback_action(
                    "LLM não sugeriu nenhuma ação", 
                    alert_data
                )
            
            # Pegamos a primeira chamada de ferramenta (a mais relevante)
            tool_call = tool_calls[0]
            function_call = tool_call.get("function", {})
            
            # Extraímos nome e argumentos da função
            function_name = function_call.get("name")
            function_args = json.loads(
                function_call.get("arguments", "{}")
            )
            
            if not function_name:
                logger.warning("Nome da função não encontrado na resposta")
                return self._create_fallback_action(
                    "Resposta inválida do LLM", 
                    alert_data
                )
            
            
            return {
                "action": function_name,
                "requires_action": function_name != "notify",
                "recommended_job_id": function_name,
                "job_parameters": function_args,
                "reason": (
                    f"Função {function_name} recomendada pelo LLM"
                ),
                "confidence": 0.9 
            }
                
        except Exception as e:
            logger.error(f"Erro ao processar resposta do Ollama: {str(e)}")
            return self._create_fallback_action(
                f"Erro ao processar resposta: {str(e)}", 
                alert_data
            )
    
    def _create_fallback_action(
        self, 
        reason: str, 
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cria uma ação de fallback para casos de erro.
        
        Args:
            reason: Motivo para o fallback
            alert_data: Dados do alerta original
            
        Returns:
            Ação de notificação formatada
        """
        host = alert_data.get('host', 'desconhecido')
        problem = alert_data.get('problem', 'Sem descrição')
        
        return {
            "action": "notify",
            "requires_action": True,
            "recommended_job_id": "notify",
            "job_parameters": {
                "team": "operations",
                "priority": "high",
                "message": (
                    f"Falha na automação para alerta em {host}: {problem}. "
                    f"Motivo: {reason}"
                )
            },
            "reason": reason,
            "confidence": 0.0
        }