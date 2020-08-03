from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import UJSONResponse
from tortoise.exceptions import DoesNotExist

from api.models import Customer, CustomerWallet
from api.schemas import OutputTransactionWithBusinessWalletListSchema
from api.utils import get_transactions_by_wallet, sort_by_key


async def get_transactions(request: Request) -> UJSONResponse:
    customer_id = request.path_params["customer_id"]
    try:
        customer = await Customer.get(id=customer_id)
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail=f"There is no customer with id {customer_id}"
        )

    deposit_transactions = (
        await customer.wallets.filter(deposit_transactions__id__not_isnull=True)
        .prefetch_related("deposit_transactions")
        .values(
            id="deposit_transactions__id",
            customer_wallet_id="id",
            amount="deposit_transactions__amount",
            status="deposit_transactions__status",
            error="deposit_transactions__error",
            description="deposit_transactions__description",
            created_at="deposit_transactions__created_at",
        )
    )

    debit_transactions = (
        await customer.wallets.filter(debit_transactions__id__not_isnull=True)
        .prefetch_related("debit_transactions")
        .values(
            id="debit_transactions__id",
            customer_wallet_id="id",
            business_wallet_id="debit_transactions__business_wallet__id",
            amount="debit_transactions__amount",
            status="debit_transactions__status",
            error="debit_transactions__error",
            description="debit_transactions__description",
            created_at="debit_transactions__created_at",
        )
    )

    response = await get_transactions_by_wallet(
        deposit_transactions, debit_transactions
    )
    return UJSONResponse({"wallets": response})


async def get_customer_wallet_transactions(request: Request) -> UJSONResponse:
    wallet_id = request.path_params["wallet_id"]

    try:
        deposit_transactions = (
            await CustomerWallet.filter(
                id=wallet_id, deposit_transactions__id__not_isnull=True
            )
            .prefetch_related("deposit_transactions")
            .values(
                id="deposit_transactions__id",
                amount="deposit_transactions__amount",
                status="deposit_transactions__status",
                error="deposit_transactions__error",
                description="deposit_transactions__description",
                created_at="deposit_transactions__created_at",
            )
        )

        debit_transactions = (
            await CustomerWallet.filter(
                id=wallet_id, debit_transactions__id__not_isnull=True
            )
            .prefetch_related("debit_transactions")
            .values(
                id="debit_transactions__id",
                business_wallet_id="debit_transactions__business_wallet__id",
                amount="debit_transactions__amount",
                status="debit_transactions__status",
                error="debit_transactions__error",
                description="debit_transactions__description",
                created_at="debit_transactions__created_at",
            )
        )

    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail=f"There is no wallet with id {wallet_id}"
        )

    transactions = deposit_transactions + debit_transactions
    transactions = [
        OutputTransactionWithBusinessWalletListSchema(**transaction).as_dict()
        for transaction in sort_by_key(transactions, "created_at")
    ]
    return UJSONResponse({"transactions": transactions})
