import httpx
import json
import time
from typing import Dict, Any, Optional, List, Tuple

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
        
        # Mapeamento entre funções e jobs do Rundeck (corrige o erro de "job não encontrado")
        self.function_job_mapping = {
            "analyze_processes": "analyze-processes",
            "cleanup_disk": "cleanup-disk",
            "restart_service": "restart-service",
            "restart_application": "restart-app",
            "notify": "notify"
        }
        
        # Registramos os jobs disponíveis para debug
        logger.info(f"Jobs disponíveis: {list(self.function_job_mapping.values())}")

    # [Os métodos existentes check_connection e _create_tools permanecem iguais]

    async def analyze_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa um alerta usando o modelo do Ollama com function calling.
        
        Args:
            alert_data: Dados do alerta do Zabbix
            
        Returns:
            Dicionário com a análise e ação recomendada
        """
        # Registra os dados recebidos em formato detalhado para debug
        logger.debug(f"Dados brutos recebidos para análise: {json.dumps(alert_data)}")
        
        # Enriquece os dados de alerta com informação contextual quando valores são genéricos
        enriched_alert = self._enrich_alert_data(alert_data)
        
        # Log do início da análise
        logger.info(
            f"Iniciando análise do alerta para {enriched_alert.get('host')} "
            f"com problema: {enriched_alert.get('problem')}"
        )
        logger.debug(f"Modelo utilizado: {self.model}")
        
        # Criamos um prompt que explica claramente a tarefa para o modelo
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(enriched_alert)
        
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
                
                # Log do tempo de resposta do modelo
                processing_time = time.time() - start_time
                logger.info(f"Ollama respondeu em {processing_time:.2f} segundos")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Log da resposta bruta do modelo para debug
                    logger.debug(f"Resposta bruta do modelo: {json.dumps(result)}")
                    
                    # Processamos a resposta buscando tool_calls
                    logger.info("Processando resposta do modelo...")
                    return self._process_ollama_response(result, enriched_alert)
                else:
                    # Em caso de falha, retornamos uma resposta padrão
                    error_msg = f"Falha ao consultar Ollama: {response.text}"
                    logger.error(error_msg)
                    return self._create_fallback_action(
                        error_msg, 
                        enriched_alert
                    )
        
        except Exception as e:
            error_msg = f"Erro ao processar com Ollama: {str(e)}"
            logger.exception(error_msg)
            return self._create_fallback_action(
                error_msg, 
                enriched_alert
            )
    
    def _enrich_alert_data(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece os dados de alerta com informações contextuais quando os valores são genéricos.
        
        Args:
            alert_data: Dados originais do alerta
            
        Returns:
            Dados de alerta enriquecidos
        """
        enriched = alert_data.copy()
        
        # Detecta se estamos lidando com dados genéricos/unknown
        is_generic = False
        if (enriched.get('host') == 'unknown-host' or 
            enriched.get('problem') == 'Unknown problem' or 
            enriched.get('severity') == 'not classified'):
            is_generic = True
            logger.warning("Detectados dados genéricos no alerta - aplicando enriquecimento")
        
        # Se os dados parecem ser genéricos, adiciona informação sobre isso
        if is_generic:
            enriched['_meta'] = {
                'is_generic_data': True,
                'generic_reason': "Valores padrão detectados no alerta",
                'generic_fields': []
            }
            
            # Identifica campos genéricos
            if enriched.get('host') == 'unknown-host':
                enriched['_meta']['generic_fields'].append('host')
                # Tenta extrair algum identificador dos outros campos
                if enriched.get('details', {}).get('ip'):
                    enriched['host'] = f"Host com IP {enriched['details']['ip']}"
                
            if enriched.get('problem') == 'Unknown problem':
                enriched['_meta']['generic_fields'].append('problem')
                # Tenta inferir o tipo de problema com base em tags ou outros campos
                if any(tag.get('tag') == 'component' and tag.get('value') == 'disk' 
                      for tag in enriched.get('tags', [])):
                    enriched['problem'] = "Possível problema de disco"
                elif any(tag.get('tag') == 'component' and tag.get('value') == 'cpu' 
                        for tag in enriched.get('tags', [])):
                    enriched['problem'] = "Possível problema de CPU"
                elif any(tag.get('tag') == 'component' and tag.get('value') == 'service' 
                        for tag in enriched.get('tags', [])):
                    enriched['problem'] = "Possível problema com serviço"
                    
            if enriched.get('severity') == 'not classified':
                enriched['_meta']['generic_fields'].append('severity')
                # Define uma severidade padrão mais útil
                enriched['severity'] = 'medium'
        
        # Garante que campos obrigatórios tenham valores significativos
        if not enriched.get('details'):
            enriched['details'] = {
                'context': 'Informações detalhadas não disponíveis',
                'generated': True
            }
            
        if not enriched.get('tags'):
            enriched['tags'] = [
                {"tag": "source", "value": "zabbix"},
                {"tag": "environment", "value": "production"}
            ]
            
        # Inclui um timestamp se não houver
        if not enriched.get('timestamp'):
            enriched['timestamp'] = int(time.time())
            
        return enriched
    
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
                function_name = call.get("function", {}).get("name")
                logger.info(f"Função chamada #{i+1}: {function_name}")
                logger.debug(f"Argumentos: {call.get('function', {}).get('arguments')}")
            
            # Vamos considerar apenas a primeira chamada de função
            first_call = tool_calls[0]
            function_name = first_call.get("function", {}).get("name")
            arguments = first_call.get("function", {}).get("arguments", "{}")
            
            # Validação e parsing dos argumentos
            parsed_arguments, is_valid = self._parse_and_validate_arguments(
                function_name, arguments
            )
            
            if not is_valid:
                logger.warning(f"Argumentos inválidos para função {function_name}")
                return self._create_fallback_action(
                    f"O modelo forneceu argumentos inválidos para a função {function_name}",
                    alert_data
                )
            
            # Log da decisão final
            logger.info(f"Ação escolhida: {function_name}")
            logger.info(f"Parâmetros validados: {parsed_arguments}")
            
            # Mapeia a função para o job correspondente no Rundeck
            job_id = self._map_function_to_job(function_name)
            requires_action = function_name != "notify"
            
            # Log do mapeamento para job
            logger.info(f"Função {function_name} mapeada para job {job_id}")
            
            return {
                "action": function_name.replace("_", "-"),
                "requires_action": requires_action,
                "recommended_job_id": job_id,
                "job_parameters": parsed_arguments,
                "reason": self._generate_reason(function_name, alert_data, parsed_arguments),
                "confidence": 0.9,  # Valor fixo de confiança
                "function_called": {
                    "name": function_name,
                    "arguments": parsed_arguments
                }
            }
        
        except Exception as e:
            logger.exception(f"Erro ao processar resposta: {str(e)}")
            return self._create_fallback_action(
                f"Erro ao processar resposta do modelo: {str(e)}",
                alert_data
            )
    
    def _parse_and_validate_arguments(
        self, 
        function_name: str, 
        arguments: Any
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Parseia e valida os argumentos da função.
        
        Args:
            function_name: Nome da função
            arguments: Argumentos da função (string ou dicionário)
            
        Returns:
            Tuple com argumentos parseados e flag de validade
        """
        parsed_args = {}
        
        # Parse string arguments if needed
        if isinstance(arguments, str):
            try:
                parsed_args = json.loads(arguments)
            except json.JSONDecodeError:
                logger.warning("Não foi possível decodificar os argumentos como JSON")
                return {}, False
        elif isinstance(arguments, dict):
            parsed_args = arguments
        else:
            logger.warning(f"Tipo de argumento não suportado: {type(arguments)}")
            return {}, False
            
        # Validate based on function
        is_valid = True
        
        if function_name == "cleanup_disk":
            if "path" not in parsed_args:
                # Path é obrigatório, adicione um valor padrão se não estiver presente
                parsed_args["path"] = "/tmp"
                logger.warning("Adicionado path padrão '/tmp' para cleanup_disk")
                
            # Garante que min_size e file_age tenham valores padrão se não especificados
            if "min_size" not in parsed_args:
                parsed_args["min_size"] = "100M"
            if "file_age" not in parsed_args:
                parsed_args["file_age"] = "7d"
                
        elif function_name == "restart_service":
            if "service_name" not in parsed_args:
                logger.warning("Parâmetro obrigatório 'service_name' ausente")
                is_valid = False
                
        elif function_name == "analyze_processes":
            if "resource_type" not in parsed_args:
                # Se faltar o tipo de recurso, assume CPU
                parsed_args["resource_type"] = "cpu"
                logger.warning("Adicionado resource_type padrão 'cpu' para analyze_processes")
                
            # Converte top_count para inteiro se for string
            if "top_count" in parsed_args and isinstance(parsed_args["top_count"], str):
                try:
                    parsed_args["top_count"] = int(parsed_args["top_count"])
                except ValueError:
                    parsed_args["top_count"] = 10
                    
            # Garante que top_count tenha um valor padrão
            if "top_count" not in parsed_args:
                parsed_args["top_count"] = 10
                
        elif function_name == "restart_application":
            if "app_name" not in parsed_args:
                logger.warning("Parâmetro obrigatório 'app_name' ausente")
                is_valid = False
                
        elif function_name == "notify":
            if "message" not in parsed_args:
                logger.warning("Parâmetro obrigatório 'message' ausente")
                is_valid = False
                
            # Valores padrão para team e priority
            if "team" not in parsed_args:
                parsed_args["team"] = "operations"
            if "priority" not in parsed_args:
                parsed_args["priority"] = "medium"
                
        return parsed_args, is_valid
    
    def _map_function_to_job(self, function_name: str) -> str:
        """
        Mapeia o nome da função para o ID do job correspondente no Rundeck.
        
        Args:
            function_name: Nome da função chamada pelo modelo
            
        Returns:
            ID do job no Rundeck
        """
        # Use o mapeamento definido na inicialização
        job_id = self.function_job_mapping.get(function_name)
        
        if not job_id:
            # Se não houver mapeamento específico, usa a convenção de substituição
            logger.warning(f"Função {function_name} não tem mapeamento explícito")
            job_id = function_name.replace("_", "-")
            
        return job_id

    def _generate_reason(
        self, 
        function_name: str, 
        alert_data: Dict[str, Any], 
        arguments: Dict[str, Any]
    ) -> str:
        """
        Gera uma justificativa para a ação escolhida.
        
        Args:
            function_name: Nome da função chamada
            alert_data: Dados do alerta
            arguments: Argumentos da função
            
        Returns:
            Texto explicando a razão da escolha
        """
        # Get host and problem details
        host = alert_data.get('host', 'desconhecido')
        problem = alert_data.get('problem', 'Unknown problem')
        
        if function_name == "cleanup_disk":
            path = arguments.get('path', '/unknown')
            return f"Disco cheio no host {host}. Limpeza recomendada no diretório {path}."
            
        elif function_name == "restart_service":
            service = arguments.get('service_name', 'desconhecido')
            return f"Serviço {service} parado ou instável no host {host}. Reinicialização recomendada."
            
        elif function_name == "analyze_processes":
            resource = arguments.get('resource_type', 'cpu')
            return f"Alta utilização de {resource} detectada no host {host}. Análise de processos recomendada."
            
        elif function_name == "restart_application":
            app = arguments.get('app_name', 'desconhecida')
            return f"Aplicação {app} com problemas no host {host}. Reinicialização recomendada."
            
        elif function_name == "notify":
            return f"Alerta requer atenção manual: {problem} no host {host}."
            
        return f"O modelo recomendou {function_name} com base na análise do alerta."

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
        
        Se você receber valores genéricos como 'unknown', 'Unknown Problem',
        ou 'not classified', ainda assim tente identificar o tipo de problema
        a partir de qualquer dado disponível, como tags, detalhes ou padrões
        no nome do host.
        
        Utilize as funções disponíveis para indicar a ação recomendada, 
        fornecendo os parâmetros corretos:
        
        1. Para problemas de disco cheio, use cleanup_disk(path="caminho")
        2. Para serviços parados, use restart_service(service_name="nome")
        3. Para alta CPU/memória, use analyze_processes(resource_type="cpu|memory")
        4. Para aplicações problemáticas, use restart_application(app_name="nome")
        5. Se não conseguir determinar ação automática, use notify(message="texto")
        
        Não adicione explicações adicionais, apenas chame a função adequada.
        """
    
    def _create_tools(self) -> List[Dict[str, Any]]:
        """
        Cria as definições de ferramentas disponíveis para o modelo LLM.
        
        Define o schema de funções que o modelo pode chamar usando
        a API de function calling do Ollama.
        
        Returns:
            Lista de definições de funções no formato esperado pelo Ollama
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "cleanup_disk",
                    "description": "Executa limpeza de disco quando há problemas de espaço",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Caminho do sistema de arquivos a limpar"
                            },
                            "min_size": {
                                "type": "string",
                                "description": "Tamanho mínimo dos arquivos a serem considerados para limpeza (ex: '100M', '1G')"
                            },
                            "file_age": {
                                "type": "string", 
                                "description": "Idade mínima dos arquivos a serem removidos (ex: '7d', '30d')"
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
                    "description": "Reinicia um serviço de sistema que está parado ou instável",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service_name": {
                                "type": "string",
                                "description": "Nome do serviço a ser reiniciado"
                            },
                            "force": {
                                "type": "boolean",
                                "description": "Se deve forçar a reinicialização"
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Timeout em segundos para esperar a reinicialização"
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
                    "description": "Analisa processos consumindo recursos excessivos",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "description": "Tipo de recurso a analisar (cpu, memory)",
                                "enum": ["cpu", "memory", "io", "network"]
                            },
                            "top_count": {
                                "type": "integer",
                                "description": "Quantidade de processos a listar"
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
                    "description": "Reinicia uma aplicação específica com problemas",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {
                                "type": "string",
                                "description": "Nome da aplicação a reiniciar"
                            },
                            "graceful": {
                                "type": "boolean",
                                "description": "Se deve aguardar processos em andamento finalizarem"
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Timeout em segundos para esperar a reinicialização"
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
                    "description": "Envia notificação para equipe quando intervenção manual é necessária",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "team": {
                                "type": "string",
                                "description": "Equipe para notificar (operations, development, security)",
                                "enum": ["operations", "development", "security", "dba", "network"]
                            },
                            "priority": {
                                "type": "string",
                                "description": "Prioridade da notificação",
                                "enum": ["low", "medium", "high", "critical"]
                            },
                            "message": {
                                "type": "string",
                                "description": "Mensagem descrevendo o problema"
                            }
                        },
                        "required": ["message"]
                    }
                }
            }
        ]

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
        ]) if details else "- Nenhum detalhe disponível"
        
        # Formatação das tags em forma limpa
        tags = alert_data.get('tags', [])
        tags_str = "\n".join([
            f"- {tag.get('tag')}: {tag.get('value')}" 
            for tag in tags if isinstance(tag, dict)
        ]) if tags else "- Nenhuma tag disponível"
        
        # Verifica se precisamos incluir uma observação sobre dados genéricos
        generic_note = ""
        if alert_data.get('_meta', {}).get('is_generic_data'):
            generic_fields = alert_data.get('_meta', {}).get('generic_fields', [])
            generic_note = f"""
            OBSERVAÇÃO: Este alerta contém alguns dados genéricos nos campos: {', '.join(generic_fields)}.
            Tente identificar o tipo de problema com base em quaisquer outros dados disponíveis.
            """
        
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
        {generic_note}
        
        Com base nas informações acima, chame a função mais apropriada para 
        resolver este problema, considerando:
        
        1. Para problemas de disco cheio ('disk', '/var', 'filesystem', 'storage'), use cleanup_disk
        2. Para serviços parados ('service', 'stopped', 'parado'), use restart_service
        3. Para alta utilização de CPU/memória ('cpu', 'memory', 'load', 'utilization'), use analyze_processes
        4. Para aplicações com problemas ('application', 'app', 'memory leak'), use restart_application
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
    