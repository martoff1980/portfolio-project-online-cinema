import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from src.config import settings
from src.database import engine, Base

# Импортируем роутеры из модулей приложения
from src.routes.auth import router as auth_router
from src.routes.movies import router as movies_router
from src.routes.cart import router as cart_router
from src.routes.orders import router as orders_router
from src.routes.payments import router as payments_router

# Отключаем стандартный Swagger и ReDoc по умолчанию для безопасности
app = FastAPI(
    title="Online Cinema API Platform",
    description="Secure REST API for an Online Cinema platform featuring user authorization, movie catalogs, shopping carts, and Stripe payments.",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

# Настройка CORS (Cross-Origin Resource Sharing) для интеграции с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажи конкретные домены (например, ['https://mycinema.com'])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры ко всем модулям бэкенда
app.include_router(auth_router)
app.include_router(movies_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payments_router)

# Инициализируем схему Basic Auth для защиты Swagger
security = HTTPBasic(auto_error=False) 

DOCS_USERNAME = os.getenv("DOCS_USERNAME")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD")

def verify_docs_credentials(
    credentials: HTTPBasicCredentials | None = Depends(security)
):
    """
    Проверяет логин и пароль для доступа к интерактивной документации.
    """
    if (
        credentials is None or
        credentials.username != settings.DOCS_USERNAME or 
        credentials.password != settings.DOCS_PASSWORD
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials for API documentation.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# --- Защищенные эндпоинты документации Swagger и OpenAPI ---

@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint(username: str = Depends(verify_docs_credentials)):
    """
    Генерирует и отдает защищенную спецификацию OpenAPI в формате JSON.
    """
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )


@app.get("/docs", include_in_schema=False)
async def protected_swagger_ui(username: str = Depends(verify_docs_credentials)):
    """
    Отрисовывает Swagger UI. При переходе по пути /docs запрашивает логин/пароль.
    """
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )


@app.get("/redoc", include_in_schema=False)
async def protected_redoc(username: str = Depends(verify_docs_credentials)):
    """
    Отрисовывает альтернативный интерфейс ReDoc (также под защитой).
    """
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )


# Базовый проверочный эндпоинт здоровья приложения
@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "service": "online-cinema-api"}