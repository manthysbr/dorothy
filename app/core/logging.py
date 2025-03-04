import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any


class LogConfig:
    """
    Configurações do sistema de logs da aplicação.
    
    Permite configurar formatos, handlers e níveis de log para
    diferentes ambientes (desenvolvimento, testes, produção).
    """
    
    # Diretório onde serão armazenados os arquivos de log
    LOG_DIR = Path("logs")
    
    # Formato dos logs
    FORMATO_SIMPLES = "%(asctime)s | %(levelname)8s | %(message)s"
    FORMATO_DETALHADO = (
        "%(asctime)s | %(levelname)8s | %(name)s | "
        "%(filename)s:%(lineno)d | %(message)s"
    )
    
    # Níveis de log disponíveis
    NIVEIS = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }


def configurar_logger(
    nome: str = "dorothy",
    nivel: str = "info",
    arquivo: Optional[str] = None,
    formato: Optional[str] = None,
) -> logging.Logger:
    """
    Configura e retorna um logger personalizado.
    
    Args:
        nome: Nome do logger
        nivel: Nível de log (debug, info, warning, error, critical)
        arquivo: Nome do arquivo de log (opcional)
        formato: Formato do log (opcional)
        
    Returns:
        Logger configurado
    """
    # Obter o nível de log adequado
    nivel_log = LogConfig.NIVEIS.get(nivel.lower(), logging.INFO)
    
    # Determinar o formato do log
    if formato is None:
        formato = (
            LogConfig.FORMATO_DETALHADO 
            if nivel_log <= logging.DEBUG 
            else LogConfig.FORMATO_SIMPLES
        )
    
    # Configurar o logger
    logger = logging.getLogger(nome)
    logger.setLevel(nivel_log)
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    # Formatter para os logs
    formatter = logging.Formatter(formato)
    
    # Handler para console com cores (para melhor visibilidade)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para arquivo (se especificado)
    if arquivo:
        # Criar diretório de logs se não existir
        os.makedirs(LogConfig.LOG_DIR, exist_ok=True)
        
        # Configurar handler de arquivo com rotação
        file_handler = RotatingFileHandler(
            LogConfig.LOG_DIR / arquivo,
            maxBytes=10_485_760,  # ~10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Configurar para registrar chamadas de exceções detalhadas
    logging.captureWarnings(True)
    
    return logger


# Inicializar o logger padrão que será importado por outros módulos
# Usamos a variável de ambiente diretamente para evitar importação circular
log_level = os.getenv("LOG_LEVEL", "info")
logger = configurar_logger(
    nome="dorothy",
    nivel=log_level,
    arquivo="dorothy.log"
)


# Funções auxiliares para logging contextualizado
def log_requisicao(
    metodo: str,
    caminho: str,
    ip: str,
    dados: Optional[Dict[str, Any]] = None
) -> None:
    """
    Registra detalhes de uma requisição recebida.
    
    Args:
        metodo: Método HTTP (GET, POST, etc)
        caminho: Caminho da requisição
        ip: Endereço IP do cliente
        dados: Dados da requisição (opcional)
    """
    logger.info(
        f"Requisição {metodo} {caminho} | IP: {ip} | "
        f"Dados: {dados if dados else '-'}"
    )


def log_erro_integracao(
    servico: str,
    operacao: str,
    erro: Exception
) -> None:
    """
    Registra erros de integração com serviços externos.
    
    Args:
        servico: Nome do serviço (Ollama, Rundeck, etc)
        operacao: Operação sendo realizada
        erro: Exceção capturada
    """
    logger.error(
        f"Erro no serviço {servico} | Operação: {operacao} | "
        f"Erro: {str(erro)}"
    )