import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from api.v1.router import router as v1_router
from configs.config import app_settings
from schemas.service import ServiceInfo

BACKEND_ENTRYPOINT = "service-b"

app = FastAPI(
    title="Service B",
    openapi_url=f"/{BACKEND_ENTRYPOINT}/openapi.json/",
    docs_url=f"/{BACKEND_ENTRYPOINT}/docs/",
)

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
