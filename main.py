"""
Ponto de entrada principal para a API Dorothy.

Este módulo configura a aplicação FastAPI e integra todos os componentes
necessários para o funcionamento da API que faz a ponte entre
Zabbix, Ollama e Rundeck.
"""
import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Importações internas
from app.api.routes import health, zabbix
from app.core.config import settings
from app.core.logging import logger, log_requisicao

# Configuração da aplicação FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Adiciona middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware para logging de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware para logging de todas as requisições.
    
    Registra o método, caminho, IP e tempo de resposta para cada requisição.
    """
    start_time = time.time()
    
    # Registra a requisição recebida
    log_requisicao(
        metodo=request.method,
        caminho=request.url.path,
        ip=request.client.host if request.client else "unknown"
    )
    
    # Processa a requisição
    response = await call_next(request)
    
    # Registra o tempo de processamento
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    
    return response


# Tratamento de exceções não capturadas
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Tratamento global de exceções não capturadas.
    
    Registra o erro e retorna uma resposta JSON padronizada.
    """
    logger.error(
        f"Erro não tratado: {str(exc)}, "
        f"Rota: {request.method} {request.url.path}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Erro interno no servidor",
            "path": request.url.path
        }
    )


# Eventos de inicialização e encerramento
@app.on_event("startup")
async def startup_event():
    """
    Evento executado na inicialização da aplicação.
    
    Realiza tarefas de inicialização como configuração de conexões.
    """
    logger.info(
        f"Iniciando API Dorothy v{settings.API_VERSION}"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento executado no encerramento da aplicação.
    
    Realiza tarefas de limpeza como fechamento de conexões.
    """
    logger.info("API Dorothy finalizada")


# Rotas raiz
@app.get("/", tags=["root"])
async def root():
    """
    Rota raiz para verificação rápida da API.
    """
    return {
        "app": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "online"
    }


# Inclusão dos routers
app.include_router(health.router, prefix="/api/v1", tags=["saúde"])
app.include_router(zabbix.router, prefix="/api/v1/zabbix", tags=["zabbix"])


# Execução direta
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )