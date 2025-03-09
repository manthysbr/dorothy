## Visão Geral Técnica

Esse é um projeto que tem como idéia automatizar boa parte do trabalho de toil em SRE, utilizando ferramentas open-source e inteligência artiticial.

Basicamente a idéia é ter uma API entre o `alert manager` ( nesse caso aqui estou utilizando Zabbix 7 ) e uma `plataforma de automação` ( aqui eu utilizei o Rundeck ), que tenha o poder de tomar decisões baseados no alerta e no histórico do host, abstraindo toda uma camada de ações manuais. 

Aqui tentei ser preditivo e generalista ao máximo, pensando apenas em operações básicas de limpeza de disco, restart de serviço, coisas comumente operadas manualmente em operações de larga escala. 

Muitos serviços tem padrões entre eles, e já vi em muitos lugares serviços simples ficarem deteriorados por longos tempos por conta de uma necessidade específica ou ação manual que poderia ser automatizada. Desde então tenho desenvolvido essa solução `ad-hoc` como projeto de estudo para fazer com que agentes especializados façam ações menores sem a necessidade de um trigger manual. 

## Formato

```
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│ AlertManager│        │             │        │ Plataforma  │
│             ├───────►│     API     ├───────►│     de      │
│  (Zabbix)   │        │             │        │ Automação   │
└─────────────┘        └──────┬──────┘        │  (Rundeck)  │
                              │               └─────────────┘
                       ┌──────▼──────┐
                       │ LLM tomando |
                       |  a decisão  │
                       │  (Ollama)   │
                       └─────────────┘
```


A API implementa um padrão de arquitetura de middleware assíncrono, posicionando-se entre sistemas de monitoramento (como Zabbix) e plataformas de automação (como Rundeck). O fluxo de dados é totalmente assíncrono, utilizando as capacidades do FastAPI e `httpx` para comunicações não-bloqueantes e escalabilidade.

### Fluxo de Processamento Detalhado

1. **Recebimento de Alertas**:
   - Alertas são recebidos via endpoints REST (`/api/v1/zabbix/alert`)
   - O payload é validado utilizando modelos Pydantic
   - Informações são normalizadas para processamento posterior
2. **Análise por LLM**:
   - O serviço `OllamaService` formata prompts especializados
   - Utiliza a técnica de "function calling" com o modelo Llama 3.2 para fornecer ao modelo as ferramentas para debugar aquela situação ( ex. limpeza de disco, restart de serviço entre outras coisas... )
   - Sistema de prompts duplos (system prompt + user prompt) para contexto e dados
   - Comunicação com Ollama via HTTP assíncrono usando `httpx`
3. **Mapeamento e Execução**:
   - O serviço `RundeckService` traduz decisões do LLM para jobs de automação
   - Implementa comunicação via webhooks para acionar scripts
   - Adiciona metadados de rastreabilidade (IDs de alerta, timestamps)
   - Oferece modo simulação para testes sem execução real

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

## Capacidades de Análise e Resolução

Até então, o projeto utiliza function calling com o LLM para determinar a ação mais apropriada entre:

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

### Conteiners
Eu utilizei como teste conteiners para simular as situações ( existe um docker compose com as configurações dentro de utils/docker ) 

#### Demo
Em docs/simulation.mp4 você pode ver uma demonstração básica do alerta saindo do zabbix, sendo recebido pela API e a API triggando o job no rundeck, resolvendo o alerta sem nenhum tipo de interação. Isso é só um exemplo de adoção mas a idéia core é remediar alertas mais comuns e preditivos, sem a necessidade de um operador humano.