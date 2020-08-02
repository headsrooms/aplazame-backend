from json import JSONDecodeError

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import UJSONResponse
from starlette.status import HTTP_201_CREATED
from tortoise.exceptions import IntegrityError
from ujson import loads

from api.constants import MALFORMED_JSON_MESSAGE
from api.models import Business
from api.schemas import (
    InputBusinessSchema,
    OutputBusinessSchema,
)


async def create_business(request: Request) -> UJSONResponse:
    try:
        payload = await request.json()
        business_data = InputBusinessSchema.parse_obj(payload)
        business = await Business.create(**business_data.dict())
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail=MALFORMED_JSON_MESSAGE)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"That email has already been used to create another account",
        )

    response = OutputBusinessSchema.from_orm(business)
    return UJSONResponse(loads(response.json()), status_code=HTTP_201_CREATED)
