## Visão Geral Técnica

Esse é um projeto que tem como idéia automatizar boa parte do trabalho de toil em SRE, utilizando ferramentas open-source e inteligência artiticial.
Basicamente a idéia é ter uma API entre o `alert manager` ( nesse caso aqui estou utilizando Zabbix 7 ) e uma `plataforma de automação` ( aqui eu utilizei o Rundeck ), que tenha o poder de tomar decisões baseados no alerta e ( em breve ) no histórico do host, abstraindo toda uma camada de ações manuais. Aqui tentei ser preditivo e generalista ao máximo, pensando apenas em operações básicas de limpeza de disco, restart de serviço, coisas comumente operadas manualmente em operações de larga escala. 



```
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│  Sistema de │        │    API      │        │ Plataforma  │
│ Monitoração ├───────►│ Middleware  ├───────►│     de      │
│  (Zabbix)   │        │  (FastAPI)  │        │ Automação   │
└─────────────┘        └──────┬──────┘        │  (Rundeck)  │
                              │               └─────────────┘
                       ┌──────▼──────┐
                       │  LLM Local  │
                       │  (Ollama)   │
                       └─────────────┘
```

## Arquitetura e Comunicação

A Dorothy implementa um padrão de arquitetura de middleware assíncrono, posicionando-se entre sistemas de monitoramento (como Zabbix) e plataformas de automação (como Rundeck). O fluxo de dados é totalmente assíncrono, utilizando as capacidades do FastAPI e `httpx` para comunicações não-bloqueantes.

### Fluxo de Processamento Detalhado

1. **Recebimento de Alertas**:
   - Alertas são recebidos via endpoints REST (`/api/v1/zabbix/alert`)
   - O payload é validado utilizando modelos Pydantic
   - Informações são normalizadas para processamento posterior

2. **Análise por LLM**:
   - O serviço `OllamaService` formata prompts especializados
   - Utiliza a técnica de "function calling" com o modelo Llama 3.2
   - Sistema de prompts duplos (system prompt + user prompt) para contexto e dados
   - Comunicação com Ollama via HTTP assíncrono usando `httpx`

3. **Mapeamento e Execução**:
   - O serviço `RundeckService` traduz decisões do LLM para jobs de automação
   - Implementa comunicação via webhooks para acionar scripts
   - Adiciona metadados de rastreabilidade (IDs de alerta, timestamps)
   - Oferece modo simulação para testes sem execução real

## Componentes Técnicos Principais

### `OllamaService`

Implementa a integração com o motor de modelo de linguagem ( llama3.2 ), utilizando uma arquitetura baseada em function calling:

```python
# Modelo do esquema de ferramentas definido para o LLM
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
                }
                # Outros parâmetros...
            },
            "required": ["path"]
        }
    }
}
```

Características técnicas:

- **Definição Estruturada de Ferramentas**: Define schema JSON para as funções que o LLM pode chamar
- **Processamento Assíncrono**: Utiliza `async/await` para não bloquear durante as chamadas ao LLM
- **Enriquecimento de Dados**: Implementa processamento contextual para lidar com dados incompletos
- **Validação de Parâmetros**: Valida e normaliza os parâmetros retornados pelo LLM
- **Mapeamento Dinâmico**: Traduz funções para jobs específicos do Rundeck

### `RundeckService`

Gerencia a comunicação com a plataforma de automação através de webhooks RESTful:

```python
# Modelo de mapeamento de jobs para webhooks
self.webhook_urls = {
    "cleanup-disk": f"{self.base_url}/api/45/webhook/CjErsoegWTqAkBT0W54n3bTNg7iIsy4I#limpeza_de_disco",
    "restart-service": f"{self.base_url}/api/45/webhook/fHhzLf806fPUOiCpdhCBM7hR5zzI8B5J#restart_servico",
    # Outros webhooks...
}
```

Características técnicas:

- **Gestão de Webhooks**: Mapeia jobs para URLs de webhook para acionar scripts no Rundeck
- **Resiliência**: Implementa fallback para webhooks não encontrados
- **Rastreabilidade**: Adiciona IDs de alerta e timestamps para correlação
- **Comunicação Assíncrona**: Utiliza `httpx.AsyncClient` para chamadas não-bloqueantes
- **Modo de Simulação**: Permite testes sem execução real através de flag de configuração

## Capacidades de Análise e Resolução

A API utiliza function calling com o LLM para determinar a ação mais apropriada entre:

1. **`cleanup_disk`**: Limpeza de sistemas de arquivos com espaço crítico
   - Parâmetros: path, min_size, file_age
   - Executa scripts que identificam e removem arquivos temporários e logs antigos

2. **`restart_service`**: Reinício de serviços de sistema parados ou instáveis
   - Parâmetros: service_name, force, timeout
   - Utiliza systemd ou outros gerenciadores de serviço para reinicialização controlada

3. **`analyze_processes`**: Análise de processos consumindo recursos excessivos
   - Parâmetros: resource_type, top_count
   - Executa comandos como `top`, `ps`, `lsof` para identificar processos problemáticos

4. **`restart_application`**: Reinicialização de aplicações específicas
   - Parâmetros: app_name, graceful, timeout
   - Gerencia reinicialização de aplicações com mínima interrupção de serviço

5. **`notify`**: Notificação para equipes quando intervenção manual é necessária
   - Parâmetros: team, priority, message
   - Envia alertas para canais de comunicação apropriados (email, chat, SMS)

## System Prompts

```python
def _create_system_prompt(self) -> str:
    """
    Cria um prompt de sistema para o modelo.
    """
    return """
    Você é um sistema especializado na análise de alertas do Zabbix e na 
    automação de respostas a incidentes. Sua tarefa é analisar alertas e
    determinar a ação mais adequada baseada nas informações fornecidas.
    
    # Instruções técnicas para análise e tomada de decisão...
    """
```

A idéia aqui é:
- Fornecer contexto para interpretação de dados incompletos ou ambíguos
- Limitar o escopo das respostas para o formato de function calling

## Mecanismos de Fallback e Resiliência

A API implementa múltiplas camadas de fallback para garantir resiliência:

1. **Fallback de Função**: Se o LLM falhar em selecionar uma função apropriada
2. **Fallback de Argumentos**: Se os parâmetros fornecidos forem inválidos ou incompletos
3. **Fallback de Webhook**: Se o webhook mapeado não for encontrado
4. **Fallback de Comunicação**: Se a chamada ao LLM ou Rundeck falhar

```python
def _create_fallback_action(self, reason: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cria uma ação de fallback para casos onde não é possível
    determinar uma ação automática ou ocorre algum erro.
    """
    # Lógica de geração de fallback...
```