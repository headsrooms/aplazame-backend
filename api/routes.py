from starlette.routing import Route

from api.endpoints.business_transactions import get_business_wallet_transactions
from api.endpoints.business_wallets import (
    create_business_wallet,
    get_business_wallet,
    debit,
)
from api.endpoints.businesses import create_business
from api.endpoints.customer_transactions import (
    get_transactions,
    get_customer_wallet_transactions,
)
from api.endpoints.customer_wallets import (
    create_customer_wallet,
    get_customer_wallet,
    deposit,
    get_wallets,
)
from api.endpoints.customers import create_customer

routes = [
    # customers
    Route("/customers/", create_customer, methods=["POST"]),
    Route(
        "/customers/{customer_id:uuid}/transactions", get_transactions, methods=["GET"]
    ),
    # customer_wallets
    Route("/customers/{customer_id:uuid}/wallets", get_wallets, methods=["GET"]),
    Route("/customers/wallets/", create_customer_wallet, methods=["POST"]),
    Route("/customers/wallets/{wallet_id:uuid}", get_customer_wallet, methods=["GET"]),
    Route(
        "/customers/wallets/{wallet_id:uuid}/transactions",
        get_customer_wallet_transactions,
        methods=["GET"],
    ),
    Route("/customers/wallets/{wallet_id:uuid}/deposit", deposit, methods=["POST"]),
    # businesses
    Route("/businesses/", create_business, methods=["POST"]),
    # business_wallets
    Route("/businesses/wallets/", create_business_wallet, methods=["POST"]),
    Route("/businesses/wallets/{wallet_id:uuid}", get_business_wallet, methods=["GET"]),
    Route(
        "/businesses/wallets/{wallet_id:uuid}/transactions",
        get_business_wallet_transactions,
        methods=["GET"],
    ),
    Route("/businesses/wallets/{wallet_id:uuid}/debit", debit, methods=["POST"]),
]
