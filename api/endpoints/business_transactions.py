from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import UJSONResponse
from tortoise.exceptions import DoesNotExist

from api.models import BusinessWallet
from api.schemas import OutputTransactionWithCustomerWalletListSchema
from api.utils import sort_by_key


async def get_business_wallet_transactions(request: Request) -> UJSONResponse:
    wallet_id = request.path_params["wallet_id"]

    try:
        transactions = (
            await BusinessWallet.get(id=wallet_id)
            .prefetch_related("transactions")
            .values(
                customer_wallet_id="transactions__customer_wallet__id",
                amount="transactions__amount",
                description="transactions__description",
                status="transactions__status",
                error="transactions__error",
                created_at="transactions__created_at",
            )
        )
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail=f"There is no wallet with id {wallet_id}"
        )

    transactions = [
        OutputTransactionWithCustomerWalletListSchema(**transaction).as_dict()
        for transaction in sort_by_key(transactions, "created_at")
    ]
    return UJSONResponse({"transactions": transactions})
