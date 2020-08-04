from decimal import Decimal
from enum import Enum
from typing import Type

from tortoise import fields, Model
from tortoise.exceptions import OperationalError
from tortoise.signals import pre_save

from api.exceptions import AmountMustBeAPositiveNumber, NotEnoughBalance


class User(Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=50)
    email = fields.CharField(max_length=50, unique=True)
    phone = fields.CharField(max_length=50, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True


class Wallet(Model):
    id = fields.UUIDField(pk=True)  # token
    # To simplify, we assume that we only use one currency.
    balance = fields.DecimalField(max_digits=19, decimal_places=4, default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True

    async def deposit_money(self, amount: Decimal, connection):
        if not amount or amount < 0:
            raise AmountMustBeAPositiveNumber(
                "The entered amount must be a positive number"
            )
        self.balance += Decimal(amount)
        await self.save(using_db=connection)


class Customer(User):
    last_name = fields.CharField(max_length=30)
    wallets: fields.ReverseRelation["CustomerWallet"]


class Business(User):
    wallet: fields.ReverseRelation["BusinessWallet"]


class CustomerWallet(Wallet):
    customer: fields.ForeignKeyRelation[Customer] = fields.ForeignKeyField(
        "models.Customer", related_name="wallets"
    )
    deposit_transactions: fields.ReverseRelation["CustomerDepositTransaction"]
    debit_transactions: fields.ReverseRelation["DebitTransaction"]

    async def debit_money(self, amount: Decimal, connection):
        if not amount or amount < 0:
            raise AmountMustBeAPositiveNumber(
                "The amount debited must be a positive number"
            )
        if amount > self.balance:
            raise NotEnoughBalance(
                "The amount debited must be less than the existing balance"
            )
        self.balance -= Decimal(amount)
        await self.save(using_db=connection)


class BusinessWallet(Wallet):
    business: fields.OneToOneRelation[Business] = fields.OneToOneField(
        "models.Business", on_delete=fields.CASCADE, related_name="wallet"
    )
    transactions: fields.ReverseRelation["DebitTransaction"]


class TransactionStatus(str, Enum):
    PENDING = "pending"
    DENIED = "denied"
    ACCEPTED = "accepted"


class Transaction(Model):
    id = fields.UUIDField(pk=True)
    amount = fields.DecimalField(max_digits=19, decimal_places=4)
    description = fields.TextField(null=True)
    status: TransactionStatus = fields.CharEnumField(
        TransactionStatus, default=TransactionStatus.PENDING
    )
    error = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        abstract = True


class CustomerDepositTransaction(Transaction):
    customer_wallet: fields.ForeignKeyRelation[CustomerWallet] = fields.ForeignKeyField(
        "models.CustomerWallet", related_name="deposit_transactions"
    )


class BusinessDepositTransaction(Transaction):
    business_wallet: fields.ForeignKeyRelation[BusinessWallet] = fields.ForeignKeyField(
        "models.BusinessWallet", related_name="deposit_transactions"
    )


class DebitTransaction(Transaction):
    customer_wallet: fields.ForeignKeyRelation[CustomerWallet] = fields.ForeignKeyField(
        "models.CustomerWallet", related_name="debit_transactions"
    )
    business_wallet: fields.ForeignKeyRelation[BusinessWallet] = fields.ForeignKeyField(
        "models.BusinessWallet", related_name="transactions"
    )


@pre_save(CustomerDepositTransaction)
async def before_customer_deposit_transaction(
    sender: Type[DebitTransaction], instance: DebitTransaction, using_db, update_fields
) -> None:
    customer_wallet = await instance.customer_wallet
    await customer_wallet.deposit_money(instance.amount, connection=using_db)
    instance.status = TransactionStatus.ACCEPTED


@pre_save(DebitTransaction)
async def before_debit_transaction(
    sender: Type[DebitTransaction], instance: DebitTransaction, using_db, update_fields
) -> None:
    customer_wallet = await instance.customer_wallet
    business_wallet = await instance.business_wallet
    business_deposit_transaction = None
    try:
        await customer_wallet.debit_money(instance.amount, using_db)
        business_deposit_transaction = await BusinessDepositTransaction.create(
            amount=instance.amount,
            description=instance.description,
            business_wallet_id=business_wallet.id,
            using_db=using_db,
        )
        instance.status = TransactionStatus.ACCEPTED
    except (NotEnoughBalance, AmountMustBeAPositiveNumber, OperationalError) as e:
        instance.status = TransactionStatus.DENIED
        instance.error = str(e)

        if business_deposit_transaction:
            business_deposit_transaction.status = TransactionStatus.DENIED
            business_deposit_transaction.error = str(e)
            await business_deposit_transaction.save(update_fields=["error"])


@pre_save(BusinessDepositTransaction)
async def before_business_deposit_transaction(
    sender: Type[BusinessDepositTransaction],
    instance: BusinessDepositTransaction,
    using_db,
    update_fields,
) -> None:
    if not update_fields:
        business_wallet = await instance.business_wallet
        await business_wallet.deposit_money(instance.amount, connection=using_db)
        instance.status = TransactionStatus.ACCEPTED
