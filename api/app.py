import uvicorn
from starlette.applications import Starlette
from tortoise.contrib.starlette import register_tortoise

from api import settings
from api.exception_handlers import exception_handlers
from api.middleware import middleware
from api.routes import routes
from api.settings import DB_URL

app = Starlette(
    debug=settings.DEBUG,
    routes=routes,
    middleware=middleware,
    exception_handlers=exception_handlers,
)

register_tortoise(
    app,
    db_url=DB_URL,
    modules={"models": ["api.models"]},
    generate_schemas=settings.GENERATE_SCHEMAS,
)

if __name__ == "__main__":
    uvicorn.run(app)
