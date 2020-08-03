import uvicorn
from starlette.applications import Starlette
from tortoise.contrib.starlette import register_tortoise

from api import settings
from api.exception_handlers import exception_handlers
from api.middleware import middleware
from api.routes import routes

app = Starlette(
    debug=settings.DEBUG,
    routes=routes,
    middleware=middleware,
    exception_handlers=exception_handlers,
)

register_tortoise(
    app,
    # db_url=f"postgres://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
    db_url="sqlite://db.sqlite",
    modules={"models": ["api.models"]},
    generate_schemas=settings.GENERATE_SCHEMAS,
)

if __name__ == "__main__":
    uvicorn.run(app)
