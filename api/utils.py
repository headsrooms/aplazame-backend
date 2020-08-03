from collections import defaultdict
from typing import Iterable, List

from api.schemas import (
    OutputTransactionWithCustomerAndBusinessWalletListSchema,
    OutputTransactionWithCustomerWalletListSchema,
)


def sort_by_key(sequence: Iterable, key: str):
    return sorted(sequence, key=lambda k: k[key], reverse=True)


async def get_transactions_by_wallet(
    deposit_transactions: List[dict], debit_transactions: List[dict]
):
    deposit_transactions = [
        OutputTransactionWithCustomerWalletListSchema(**transaction).as_dict()
        for transaction in deposit_transactions
    ]
    debit_transactions = [
        OutputTransactionWithCustomerAndBusinessWalletListSchema(
            **transaction
        ).as_dict()
        for transaction in debit_transactions
    ]
    transactions = deposit_transactions + debit_transactions
    transactions = sort_by_key(transactions, "created_at")

    transactions_by_wallet = defaultdict(list)
    for transaction in transactions:
        key = transaction.pop("customer_wallet_id")
        transactions_by_wallet[key].append(transaction)

    response = [
        {"id": wallet_id, "transactions": transactions}
        for wallet_id, transactions in transactions_by_wallet.items()
    ]
    return response
