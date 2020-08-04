from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from tortoise.contrib.pydantic import pydantic_model_creator, pydantic_queryset_creator

from api.models import (
    Customer,
    CustomerWallet,
    BusinessWallet,
    Business,
    CustomerDepositTransaction,
    DebitTransaction,
    TransactionStatus,
)

# Customer
InputCustomerSchema = pydantic_model_creator(
    Customer, exclude=("id", "wallets", "created_at", "modified_at")
)
OutputCustomerSchema = pydantic_model_creator(Customer)

# CustomerWallet
OutputCustomerWalletSchema = pydantic_model_creator(CustomerWallet)
OutputCustomerWalletListSchema = pydantic_queryset_creator(CustomerWallet)

# Business
InputBusinessSchema = pydantic_model_creator(
    Business, exclude=("id", "wallets", "created_at", "modified_at")
)
OutputBusinessSchema = pydantic_model_creator(Business)

# BusinessWallet
OutputBusinessWalletSchema = pydantic_model_creator(BusinessWallet)

# CustomerDepositTransaction
InputDepositTransactionSchema = pydantic_model_creator(
    CustomerDepositTransaction,
    exclude=("id", "customer_wallet", "created_at", "status", "error"),
)
OutputDepositTransactionSchema = pydantic_model_creator(CustomerDepositTransaction)
OutputDepositTransactionListSchema = pydantic_queryset_creator(
    CustomerDepositTransaction
)

# DebitTransaction
InputDebitTransactionSchema = pydantic_model_creator(
    DebitTransaction,
    exclude=(
        "id",
        "customer_wallet",
        "business_wallet",
        "created_at",
        "status",
        "error",
    ),
)
OutputDebitTransactionSchema = pydantic_model_creator(DebitTransaction)
OutputDebitTransactionListSchema = pydantic_queryset_creator(DebitTransaction)


# transactions
@dataclass(frozen=True)
class OutputTransactionListSchema:
    amount: Decimal
    description: str
    status: TransactionStatus
    created_at: datetime
    error: str = ""

    def as_dict(self):
        output = asdict(self)
        result = {}

        for k, v in output.items():
            if not v:
                pass  # no store in the result
            elif k == "amount":
                result[k] = float(v)
            elif k == "status":  # enum
                result[k] = v.value
            else:
                result[k] = str(v)

        return result


@dataclass(frozen=True)
class OutputTransactionWithBusinessWalletListSchema(OutputTransactionListSchema):
    id: uuid4 = None
    business_wallet_id: uuid4 = None


@dataclass(frozen=True)
class OutputTransactionWithCustomerWalletListSchema(OutputTransactionListSchema):
    id: uuid4 = None
    customer_wallet_id: uuid4 = None


@dataclass(frozen=True)
class OutputTransactionWithCustomerAndBusinessWalletListSchema(
    OutputTransactionWithBusinessWalletListSchema
):
    id: uuid4 = None
    customer_wallet_id: uuid4 = None
