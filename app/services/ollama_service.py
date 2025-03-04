import httpx
import json
import time  # Adicionando a importação necessária
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
    
    # Método analyze_alert corretamente indentado como parte da classe
    async def analyze_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa um alerta usando o modelo do Ollama com function calling.
        
        Args:
            alert_data: Dados do alerta do Zabbix
            
        Returns:
            Dicionário com a análise e ação recomendada
        """
        # Log do início da análise
        logger.info(
            f"Iniciando análise do alerta para {alert_data.get('host')} "
            f"com problema: {alert_data.get('problem')}"
        )
        logger.debug(f"Modelo utilizado: {self.model}")
        
        # Criamos um prompt que explica claramente a tarefa para o modelo
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(alert_data)
        
        # Log dos prompts para debug
        logger.debug(f"System prompt: {system_prompt[:200]}...")
        logger.debug(f"User prompt: {user_prompt[:200]}...")
        
        try:
            logger.info("Enviando requisição para Ollama...")
            start_time = time.time()
            
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
                
                # Log do tempo de resposta
                processing_time = time.time() - start_time
                logger.info(f"Ollama respondeu em {processing_time:.2f} segundos")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Log da resposta bruta do modelo para debug
                    logger.debug(f"Resposta bruta do modelo: {json.dumps(result)}")
                    
                    # Processamos a resposta buscando tool_calls
                    logger.info("Processando resposta do modelo...")
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
    
    def _process_ollama_response(
        self, 
        result: Dict[str, Any], 
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Processa a resposta do Ollama e extrai as funções chamadas pelo modelo.
        
        Args:
            result: Resposta do Ollama
            alert_data: Dados do alerta original
            
        Returns:
            Ação a ser executada no Rundeck
        """
        try:
            # Extrai a mensagem de resposta
            message = result.get("message", {})
            logger.debug(f"Conteúdo da mensagem: {message.get('content')}")
            
            # Verifica se o modelo chamou alguma função
            tool_calls = message.get("tool_calls", [])
            
            if not tool_calls:
                logger.warning("O modelo não chamou nenhuma função")
                return self._create_fallback_action(
                    "O modelo não recomendou nenhuma ação específica",
                    alert_data
                )
            
            # Log das funções chamadas
            for i, call in enumerate(tool_calls):
                logger.info(f"Função chamada #{i+1}: {call.get('function', {}).get('name')}")
                logger.debug(f"Argumentos: {call.get('function', {}).get('arguments')}")
            
            # Vamos considerar apenas a primeira chamada de função
            first_call = tool_calls[0]
            function_name = first_call.get("function", {}).get("name")
            arguments = first_call.get("function", {}).get("arguments", "{}")
            
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    logger.warning("Não foi possível decodificar os argumentos como JSON")
                    arguments = {}
            
            # Log da decisão final
            logger.info(f"Ação escolhida: {function_name}")
            logger.info(f"Parâmetros: {arguments}")
            
            # Mapeia a função para a ação correspondente
            action_name = function_name.replace("_", "-")
            requires_action = action_name != "notify"
            
            return {
                "action": action_name,
                "requires_action": requires_action,
                "recommended_job_id": action_name,
                "job_parameters": arguments,
                "reason": f"O modelo recomendou {action_name} com base na análise do alerta",
                "confidence": 0.9,  # Não temos um valor real de confiança
                "raw_tool_call": first_call  # Incluímos a chamada bruta para referência
            }
        
        except Exception as e:
            logger.exception(f"Erro ao processar resposta: {str(e)}")
            return self._create_fallback_action(
                f"Erro ao processar resposta do modelo: {str(e)}",
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
    
    import httpx
import json
import time  # Adicionando a importação necessária
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
    
    # Método analyze_alert corretamente indentado como parte da classe
    async def analyze_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa um alerta usando o modelo do Ollama com function calling.
        
        Args:
            alert_data: Dados do alerta do Zabbix
            
        Returns:
            Dicionário com a análise e ação recomendada
        """
        # Log do início da análise
        logger.info(
            f"Iniciando análise do alerta para {alert_data.get('host')} "
            f"com problema: {alert_data.get('problem')}"
        )
        logger.debug(f"Modelo utilizado: {self.model}")
        
        # Criamos um prompt que explica claramente a tarefa para o modelo
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(alert_data)
        
        # Log dos prompts para debug
        logger.debug(f"System prompt: {system_prompt[:200]}...")
        logger.debug(f"User prompt: {user_prompt[:200]}...")
        
        try:
            logger.info("Enviando requisição para Ollama...")
            start_time = time.time()
            
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
                
                # Log do tempo de resposta
                processing_time = time.time() - start_time
                logger.info(f"Ollama respondeu em {processing_time:.2f} segundos")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Log da resposta bruta do modelo para debug
                    logger.debug(f"Resposta bruta do modelo: {json.dumps(result)}")
                    
                    # Processamos a resposta buscando tool_calls
                    logger.info("Processando resposta do modelo...")
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
    
    def _process_ollama_response(
        self, 
        result: Dict[str, Any], 
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Processa a resposta do Ollama e extrai as funções chamadas pelo modelo.
        
        Args:
            result: Resposta do Ollama
            alert_data: Dados do alerta original
            
        Returns:
            Ação a ser executada no Rundeck
        """
        try:
            # Extrai a mensagem de resposta
            message = result.get("message", {})
            logger.debug(f"Conteúdo da mensagem: {message.get('content')}")
            
            # Verifica se o modelo chamou alguma função
            tool_calls = message.get("tool_calls", [])
            
            if not tool_calls:
                logger.warning("O modelo não chamou nenhuma função")
                return self._create_fallback_action(
                    "O modelo não recomendou nenhuma ação específica",
                    alert_data
                )
            
            # Log das funções chamadas
            for i, call in enumerate(tool_calls):
                logger.info(f"Função chamada #{i+1}: {call.get('function', {}).get('name')}")
                logger.debug(f"Argumentos: {call.get('function', {}).get('arguments')}")
            
            # Vamos considerar apenas a primeira chamada de função
            first_call = tool_calls[0]
            function_name = first_call.get("function", {}).get("name")
            arguments = first_call.get("function", {}).get("arguments", "{}")
            
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    logger.warning("Não foi possível decodificar os argumentos como JSON")
                    arguments = {}
            
            # Log da decisão final
            logger.info(f"Ação escolhida: {function_name}")
            logger.info(f"Parâmetros: {arguments}")
            
            # Mapeia a função para a ação correspondente
            action_name = function_name.replace("_", "-")
            requires_action = action_name != "notify"
            
            return {
                "action": action_name,
                "requires_action": requires_action,
                "recommended_job_id": action_name,
                "job_parameters": arguments,
                "reason": f"O modelo recomendou {action_name} com base na análise do alerta",
                "confidence": 0.9,  # Não temos um valor real de confiança
                "raw_tool_call": first_call  # Incluímos a chamada bruta para referência
            }
        
        except Exception as e:
            logger.exception(f"Erro ao processar resposta: {str(e)}")
            return self._create_fallback_action(
                f"Erro ao processar resposta do modelo: {str(e)}",
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
        Cria um prompt específico para o alerta recebido.
        
        Args:
            alert_data: Dados do alerta do Zabbix
            
        Returns:
            Prompt formatado para o usuário
        """
        # Extraímos os dados principais do alerta
        host = alert_data.get('host', 'desconhecido')
        problem = alert_data.get('problem', 'Problema não especificado')
        severity = alert_data.get('severity', 'não especificada')
        status = alert_data.get('status', 'PROBLEM')
        
        # Formatação dos detalhes em forma limpa
        details = alert_data.get('details', {})
        details_str = "\n".join([
            f"- {key}: {value}" for key, value in details.items()
        ])
        
        # Formatação das tags em forma limpa
        tags = alert_data.get('tags', [])
        tags_str = "\n".join([
            f"- {tag.get('tag')}: {tag.get('value')}" 
            for tag in tags if isinstance(tag, dict)
        ])
        
        # Construção do prompt final
        return f"""
        Analise o seguinte alerta do Zabbix e determine a melhor ação a ser 
        executada:
        
        Host: {host}
        Problema: {problem}
        Severidade: {severity}
        Status: {status}
        
        Detalhes adicionais:
        {details_str}
        
        Tags:
        {tags_str}
        
        Com base nas informações acima, chame a função mais apropriada para 
        resolver este problema. Considere:
        
        1. Para problemas de disco cheio, use cleanup_disk
        2. Para serviços parados, use restart_service
        3. Para alta utilização de CPU ou memória, use analyze_processes
        4. Para aplicações com vazamento de memória, use restart_application
        5. Se nenhuma ação automática for apropriada, use notify
        """
    
    def _create_fallback_action(
        self, 
        reason: str, 
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cria uma ação de fallback para casos onde não é possível
        determinar uma ação automática ou ocorre algum erro.
        
        Args:
            reason: Motivo pelo qual a ação de fallback está sendo criada
            alert_data: Dados do alerta original
            
        Returns:
            Ação de notificação formatada
        """
        # Extraímos informações básicas para a mensagem
        host = alert_data.get('host', 'desconhecido')
        problem = alert_data.get('problem', 'Problema não especificado')
        
        # Formatamos a mensagem de notificação
        message = (
            f"Alerta em {host}: {problem}. "
            f"Não foi possível determinar uma ação automática. "
            f"Motivo: {reason}"
        )
        
        # Determinamos a equipe com base nas tags, se disponíveis
        team = "operations"  # Valor padrão
        for tag in alert_data.get('tags', []):
            if isinstance(tag, dict) and tag.get('tag') == 'team':
                team = tag.get('value', team)
        
        # Determinamos a prioridade com base na severidade
        severity = alert_data.get('severity', 'medium').lower()
        priority = "high" if severity in ['critical', 'high'] else "medium"
        
        return {
            "action": "notify",
            "requires_action": False,
            "recommended_job_id": "notify",
            "job_parameters": {
                "team": team,
                "priority": priority,
                "message": message
            },
            "reason": reason,
            "confidence": 0.0,
            "original_alert": {
                "host": host,
                "problem": problem,
                "severity": alert_data.get('severity', 'desconhecida')
            }
        }    
    