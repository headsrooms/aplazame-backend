from json import JSONDecodeError

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import UJSONResponse
from starlette.status import HTTP_201_CREATED
from tortoise.exceptions import DoesNotExist, OperationalError
from tortoise.transactions import in_transaction
from ujson import loads

from api.constants import MALFORMED_JSON_MESSAGE
from api.exceptions import AmountMustBeAPositiveNumber, NotEnoughBalance, UnexpectedError
from api.models import (
    CustomerWallet,
    DebitTransaction,
    Business,
    BusinessWallet,
    TransactionStatus,
)
from api.schemas import (
    InputDebitTransactionSchema,
    OutputDebitTransactionSchema,
    OutputBusinessWalletSchema,
)


async def create_business_wallet(request: Request) -> UJSONResponse:
    try:
        payload = await request.json()
        business_id = payload["business_id"]
        _ = await Business.get(id=business_id)
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail=MALFORMED_JSON_MESSAGE)
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"There is no 'business_id' key in the json of the request",
        )
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail=f"There is no business with id {business_id}"
        )

    wallet = await BusinessWallet.create(business_id=business_id)
    response = OutputBusinessWalletSchema.from_orm(wallet)
    return UJSONResponse(loads(response.json()), status_code=HTTP_201_CREATED)


async def get_business_wallet(request: Request) -> UJSONResponse:
    wallet_id = request.path_params["wallet_id"]

    try:
        wallet = await BusinessWallet.get(id=wallet_id)
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail=f"There is no wallet with id {wallet_id}"
        )

    response = OutputBusinessWalletSchema.from_orm(wallet)
    return UJSONResponse(loads(response.json()))


async def debit(request: Request) -> UJSONResponse:
    business_wallet_id = request.path_params["wallet_id"]

    try:
        payload = await request.json()
        customer_wallet_id = payload.pop("customer_wallet_id")

        # check wallets existence
        business_wallet = await BusinessWallet.get_or_none(id=business_wallet_id)
        customer_wallet = await CustomerWallet.get_or_none(id=customer_wallet_id)
        if not business_wallet:
            raise HTTPException(
                status_code=404,
                detail=f"There is no wallet with id {business_wallet_id}",
            )
        if not customer_wallet:
            raise HTTPException(
                status_code=404,
                detail=f"There is no customer wallet with id {customer_wallet_id}",
            )

        transaction_data = InputDebitTransactionSchema.parse_obj(payload)

        async with in_transaction() as connection:
            transaction = await DebitTransaction.create(
                **transaction_data.dict(),
                customer_wallet_id=customer_wallet_id,
                business_wallet_id=business_wallet_id,
                using_db=connection,
            )
            if transaction.status == TransactionStatus.DENIED:
                raise UnexpectedError(transaction.error)
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail=MALFORMED_JSON_MESSAGE)
    except (AmountMustBeAPositiveNumber, NotEnoughBalance, OperationalError, UnexpectedError) as e:
        raise HTTPException(status_code=409, detail=str(e))

    response = OutputDebitTransactionSchema.from_orm(transaction)
    response = loads(response.json())
    response["id"] = str(transaction.id)
    return UJSONResponse(response, status_code=HTTP_201_CREATED)
