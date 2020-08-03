import asyncio
from dataclasses import asdict
from random import uniform

import pytest
from faker import Faker
from starlette.testclient import TestClient
from tortoise.transactions import in_transaction

from api.app import app
from api.models import (
    Customer,
    Business,
    CustomerWallet,
    DebitTransaction,
    BusinessWallet,
    DepositTransaction,
)
from api.schemas import (
    InputCustomerSchema,
    OutputCustomerSchema,
    OutputBusinessSchema,
    InputBusinessSchema,
)


@pytest.yield_fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def client(request):
    with TestClient(app) as c:
        yield c


def customer_data():
    faker = Faker()
    return InputCustomerSchema(
        name=faker.first_name(),
        last_name=faker.last_name(),
        email=faker.email(),
        phone=faker.phone_number(),
    )


@pytest.mark.asyncio
@pytest.fixture
async def random_customer():
    customer = await Customer.create(**customer_data().dict())
    yield customer

    await customer.delete()


def business_data():
    faker = Faker()
    return InputBusinessSchema(
        name=faker.company(), email=faker.email(), phone=faker.phone_number(),
    )


@pytest.mark.asyncio
@pytest.fixture
async def random_business():
    business = await Business.create(**business_data().dict())
    yield business

    await business.delete()


@pytest.mark.asyncio
@pytest.fixture(scope="session", params=[1000])
async def random_customers(request):
    async def fin():
        async with in_transaction() as connection:
            for customer in customers_db:
                await customer.delete(using_db=connection)

    customers_db = []
    customers = []
    request.addfinalizer(fin)

    async with in_transaction() as connection:
        for _ in range(request.param):
            customer_data = customer_data()
            customer = Customer(**asdict(customer_data))
            await customer.save(using_db=connection)
            customers_db.append(customer)
            customers.append(OutputCustomerSchema.from_orm(customer).dict())

    yield customers_db, customers


@pytest.mark.asyncio
@pytest.fixture(scope="session", params=[1000])
async def random_businesses(request):
    async def fin():
        async with in_transaction() as connection:
            for business in businesses_db:
                await business.delete(using_db=connection)

    businesses_db = []
    businesses = []
    request.addfinalizer(fin)

    async with in_transaction() as connection:
        for _ in range(request.param):
            business_data = business_data()
            business = Customer(**asdict(business_data))
            await business.save(using_db=connection)
            businesses_db.append(business)
            businesses.append(OutputBusinessSchema.from_orm(business).dict())

    yield businesses_db, businesses


@pytest.mark.asyncio
@pytest.fixture
async def customer_wallet(random_customer):
    wallet = await CustomerWallet.create(customer_id=random_customer.id)
    yield wallet

    await wallet.delete()


@pytest.mark.asyncio
@pytest.fixture
async def customer_wallets(random_customer):
    wallets = [
        await CustomerWallet.create(customer_id=random_customer.id) for _ in range(10)
    ]
    yield wallets

    for wallet in wallets:
        await wallet.delete()


@pytest.mark.asyncio
@pytest.fixture
async def business_wallet(random_business):
    wallet = await BusinessWallet.create(business_id=random_business.id)
    yield wallet

    await wallet.delete()


@pytest.mark.asyncio
@pytest.fixture
async def business_wallets(random_business):
    wallets = [
        await BusinessWallet.create(business_id=random_business.id) for _ in range(10)
    ]
    yield wallets

    for wallet in wallets:
        await wallet.delete()


@pytest.mark.asyncio
@pytest.fixture
async def deposit_transaction_data(customer_wallet):
    faker = Faker()
    yield {
        "amount": uniform(0, 200_000),
        "description": faker.text(),
        "customer_wallet_id": str(customer_wallet.id),
    }


@pytest.mark.asyncio
@pytest.fixture
async def n_deposit_transaction_data(customer_wallet, n=10):
    faker = Faker()

    yield [
        {
            "amount": uniform(0, 200_000),
            "description": faker.text(),
            "customer_wallet_id": str(customer_wallet.id),
        }
        for _ in range(n)
    ]


@pytest.mark.asyncio
@pytest.fixture
async def debit_transaction_data(customer_wallet, business_wallet):
    faker = Faker()

    yield {
        "amount": uniform(0, 200_000),
        "description": faker.text(),
        "customer_wallet_id": str(customer_wallet.id),
        "business_wallet_id": str(business_wallet.id),
    }


@pytest.mark.asyncio
@pytest.fixture
async def n_debit_transaction_data(customer_wallet, business_wallet, n=10):
    faker = Faker()

    yield [
        {
            "amount": uniform(0, 200_000),
            "description": faker.text(),
            "customer_wallet_id": str(customer_wallet.id),
            "business_wallet_id": str(business_wallet.id),
        }
        for _ in range(n)
    ]


@pytest.mark.asyncio
@pytest.fixture
async def ten_deposit_transactions_in_a_wallet(n_deposit_transaction_data):
    transactions = [
        await DepositTransaction.create(**deposit_transaction_data)
        for deposit_transaction_data in n_deposit_transaction_data
    ]
    yield transactions

    for transaction in transactions:
        await transaction.delete()


@pytest.mark.asyncio
@pytest.fixture
async def ten_debit_transactions_in_a_wallet(n_debit_transaction_data):
    transactions = [
        await DebitTransaction.create(**debit_transaction_data)
        for debit_transaction_data in n_debit_transaction_data
    ]
    yield transactions

    for transaction in transactions:
        await transaction.delete()
