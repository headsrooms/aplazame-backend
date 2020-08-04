import asyncio
from asyncio import sleep
from random import uniform

import pytest


async def create_debit(
    client, business_wallet_id: str, customer_wallet_id, amount: float
):
    amount = round(amount, 3)
    payload = {
        "customer_wallet_id": customer_wallet_id,
        "amount": amount,
        "description": "Cobro",
    }
    await sleep(uniform(0.0001, 0.01))  # to introduce more delays
    r = await client.post(
        f"/businesses/wallets/{business_wallet_id}/debit/", json=payload
    )

    if r.status_code == 201:
        result = "debit", amount
    else:
        result = "fail", amount

    await check_balance_is_positive(client, customer_wallet_id)

    return result


async def create_deposit(client, customer_wallet_id: str, amount: float):
    amount = round(amount, 3)
    payload = {"amount": amount, "description": "Ingreso"}

    await sleep(uniform(0.0001, 0.01))  # to introduce more delays
    r = await client.post(
        f"/customers/wallets/{customer_wallet_id}/deposit/", json=payload
    )
    assert r.status_code == 201

    result = "deposit", amount

    return result


async def check_balance_is_positive(client, customer_wallet_id):
    balance = await get_customer_balance(client, customer_wallet_id)

    assert balance >= 0


def has_duplicates(iterable):
    if len(iterable) == len(set(iterable)):
        return False
    return True


async def check_transactions(client, customer_wallet_id):
    r = await client.get(f"/customers/wallets/{customer_wallet_id}/transactions/")
    assert r.status_code == 200

    r = r.json()
    transactions = r["transactions"]
    transactions_ids = [transaction["id"] for transaction in transactions]
    transactions_amounts = [transaction["amount"] for transaction in transactions]
    assert not has_duplicates(transactions_ids)
    assert not has_duplicates(transactions_amounts)


def get_total_deposit_and_total_debit(result):
    total_deposit = 0
    total_debit = 0
    for type_amount in result:
        if type_amount:
            transaction_type, amount = type_amount
            if transaction_type == "deposit":
                total_deposit += amount
            elif transaction_type == "debit":
                total_debit += amount
    return total_deposit, total_debit


async def get_customer_balance(client, customer_wallet_id):
    r = await client.get(f"/customers/wallets/{customer_wallet_id}/")
    assert r.status_code == 200
    final_balance = r.json()["balance"]
    return final_balance


async def get_business_balance(client, business_wallet_id):
    r = await client.get(f"businesses/wallets/{business_wallet_id}/")
    assert r.status_code == 200
    business_balance = r.json()["balance"]
    return business_balance


@pytest.mark.asyncio
async def test_try_to_create_negative_balance(
    async_client, business_wallet, customer_wallet
):
    deposit_aws = []
    debit_aws = []
    customer_wallet_id = str(customer_wallet.id)
    business_wallet_id = str(business_wallet.id)

    for _ in range(1_000):
        debit_amount = uniform(0, 100_000)
        deposit_amount = uniform(0, 100_000)
        deposit_aws.append(
            create_deposit(async_client, customer_wallet_id, deposit_amount)
        )
        debit_aws.append(
            create_debit(
                async_client, business_wallet_id, customer_wallet_id, debit_amount
            )
        )

    aws = deposit_aws + debit_aws
    result = await asyncio.gather(*aws)

    total_deposit, total_debit = get_total_deposit_and_total_debit(result)
    final_customer_balance = await get_customer_balance(
        async_client, customer_wallet_id
    )
    final_business_balance = await get_business_balance(
        async_client, business_wallet_id
    )

    assert final_customer_balance == round(total_deposit - total_debit, 3)
    assert final_business_balance == round(total_debit, 3)


@pytest.mark.asyncio
async def test_try_to_create_duplicated_payments(
    async_client, business_wallet, customer_wallet
):
    deposit_aws = []
    debit_aws = []
    customer_wallet_id = str(customer_wallet.id)
    business_wallet_id = str(business_wallet.id)
    for _ in range(1_000):
        debit_amount = uniform(0, 100_000)
        deposit_amount = uniform(0, 100_000)
        deposit_aws.append(
            create_deposit(async_client, customer_wallet_id, deposit_amount)
        )
        debit_aws.append(
            create_debit(
                async_client, business_wallet_id, customer_wallet_id, debit_amount
            )
        )
    aws = deposit_aws + debit_aws
    await asyncio.gather(*aws)
    await check_transactions(async_client, customer_wallet_id)
