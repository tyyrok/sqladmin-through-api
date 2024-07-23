import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from api.admin.admin import load_admin_site
from api.v1.router import router as v1_router
from configs.config import app_settings
from databases.database import async_engine
from schemas.service import ServiceInfo
from api.admin.custom_admin import CustomAdmin

BACKEND_ENTRYPOINT = "service-a"

app = FastAPI(
    title="Service A",
    openapi_url=f"/{BACKEND_ENTRYPOINT}/openapi.json/",
    docs_url=f"/{BACKEND_ENTRYPOINT}/docs/",
)


admin = CustomAdmin(
    app,
    async_engine,
    title="Квиз Админ Панель",
    base_url=f"/{BACKEND_ENTRYPOINT}/admin",
    templates_dir="service_a/src/templates/sqladmin",
)
load_admin_site(admin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix=f"/{BACKEND_ENTRYPOINT}")


@app.get(f"/{BACKEND_ENTRYPOINT}/", response_model=ServiceInfo)
async def root() -> ServiceInfo:
    return ServiceInfo(
        name_service=app_settings.SERVICE_NAME,
        version=app_settings.SERVICE_VERSION,
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # noqa: S104
        port=app_settings.SERVICE_PORT,
        reload=True,
        forwarded_allow_ips="*",
    )
