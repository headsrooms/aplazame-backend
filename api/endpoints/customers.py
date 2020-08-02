from json import JSONDecodeError

from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import UJSONResponse
from starlette.status import HTTP_201_CREATED
from tortoise.exceptions import IntegrityError
from ujson import loads

from api.constants import MALFORMED_JSON_MESSAGE
from api.models import Customer
from api.schemas import (
    InputCustomerSchema,
    OutputCustomerSchema,
)


async def create_customer(request: Request) -> UJSONResponse:
    try:
        payload = await request.json()
        customer_data = InputCustomerSchema.parse_obj(payload)
        customer = await Customer.create(**customer_data.dict())
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail=MALFORMED_JSON_MESSAGE)
    except ValidationError as e:
        raise HTTPException(
            status_code=400, detail=str(e),
        )
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"That email has already been used to create another account",
        )

    response = OutputCustomerSchema.from_orm(customer)
    return UJSONResponse(loads(response.json()), status_code=HTTP_201_CREATED)
