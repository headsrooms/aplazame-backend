from json import JSONDecodeError

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import UJSONResponse
from starlette.status import HTTP_201_CREATED
from tortoise.exceptions import DoesNotExist, OperationalError
from tortoise.transactions import in_transaction
from ujson import loads

from api.constants import MALFORMED_JSON_MESSAGE
from api.exceptions import AmountMustBeAPositiveNumber, UnexpectedError
from api.models import (
    Customer,
    CustomerWallet,
    CustomerDepositTransaction,
    TransactionStatus,
)
from api.schemas import (
    OutputCustomerWalletSchema,
    InputDepositTransactionSchema,
    OutputDepositTransactionSchema,
    OutputCustomerWalletListSchema,
)
from api.utils import sort_by_key


async def get_wallets(request: Request) -> UJSONResponse:
    customer_id = request.path_params["customer_id"]
    wallets = CustomerWallet.filter(customer_id=customer_id)
    response = await OutputCustomerWalletListSchema.from_queryset(wallets)
    response = sort_by_key(loads(response.json()), "modified_at")
    return UJSONResponse({"wallets": response})


async def create_customer_wallet(request: Request) -> UJSONResponse:
    try:
        payload = await request.json()
        customer_id = payload["customer_id"]
        _ = await Customer.get(id=customer_id)
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail=MALFORMED_JSON_MESSAGE)
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"There is no 'customer_id' key in the json of the request",
        )
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail=f"There is no customer with id {customer_id}"
        )

    wallet = await CustomerWallet.create(customer_id=customer_id)
    response = OutputCustomerWalletSchema.from_orm(wallet)
    return UJSONResponse(loads(response.json()), status_code=HTTP_201_CREATED)


async def get_customer_wallet(request: Request) -> UJSONResponse:
    wallet_id = request.path_params["wallet_id"]

    try:
        wallet = await CustomerWallet.get(id=wallet_id)
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail=f"There is no wallet with id {wallet_id}"
        )

    response = OutputCustomerWalletSchema.from_orm(wallet)
    return UJSONResponse(loads(response.json()))


async def deposit(request: Request) -> UJSONResponse:
    wallet_id = request.path_params["wallet_id"]

    try:
        _ = await CustomerWallet.get(id=wallet_id)
        payload = await request.json()
        transaction_data = InputDepositTransactionSchema.parse_obj(payload)

        async with in_transaction() as connection:
            transaction = await CustomerDepositTransaction.create(
                **transaction_data.dict(),
                customer_wallet_id=wallet_id,
                using_db=connection,
            )

            if transaction.status == TransactionStatus.DENIED:
                raise UnexpectedError(transaction.error)
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail=f"There is no wallet with id {wallet_id}"
        )
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail=MALFORMED_JSON_MESSAGE)
    except (AmountMustBeAPositiveNumber, OperationalError, UnexpectedError) as e:
        raise HTTPException(status_code=409, detail=str(e))

    response = OutputDepositTransactionSchema.from_orm(transaction)
    response = loads(response.json())
    response["id"] = str(transaction.id)
    return UJSONResponse(response, status_code=HTTP_201_CREATED)
