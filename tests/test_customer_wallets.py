from random import uniform
from uuid import uuid4

import pytest
from requests import HTTPError
from ujson import loads

from api.schemas import OutputCustomerWalletSchema


def test_get_ten_wallets(client, random_customer, customer_wallets):
    received_wallets = client.get(
        f"/customers/{str(random_customer.id)}/wallets"
    ).json()["wallets"]
    customer_wallets = [
        loads(OutputCustomerWalletSchema.from_orm(wallet).json())
        for wallet in customer_wallets
    ]

    assert all(
        [customer_wallet in received_wallets for customer_wallet in customer_wallets]
    )


def test_create_customer_wallet(client, random_customer):
    payload = {"customer_id": str(random_customer.id)}
    response = client.post("/customers/wallets/", json=payload)
    wallet = response.json()
    assert wallet["id"]


def test_try_to_create_customer_wallet_without_customer_id(client):
    payload = {}
    response = client.post("/customers/wallets/", json=payload)

    with pytest.raises(HTTPError):
        response.raise_for_status()

    assert response.status_code == 400


def test_try_to_create_customer_wallet_with_not_registered_customer_id(client):
    payload = {"customer_id": str(uuid4())}
    response = client.post("/customers/wallets/", json=payload)

    with pytest.raises(HTTPError):
        response.raise_for_status()

    assert response.status_code == 404


def test_get_a_wallet(client, customer_wallets):
    customer_wallets = [
        loads(OutputCustomerWalletSchema.from_orm(wallet).json())
        for wallet in customer_wallets
    ]

    for wallet in customer_wallets:
        response = client.get(f"/customers/wallets/{wallet['id']}")

        assert response.status_code == 200


def test_try_to_get_a_non_existent_wallet(client):
    response = client.get(f"/customers/wallets/{str(uuid4())}")

    with pytest.raises(HTTPError):
        response.raise_for_status()

    assert response.status_code == 404


def test_deposit_money(client, customer_wallet):
    wallet_id = str(customer_wallet.id)
    payload = {"amount": uniform(0, 200_000), "description": "First entry"}
    response = client.post(f"/customers/wallets/{wallet_id}/deposit", json=payload)

    assert response.status_code == 201
    json_response = response.json()
    assert json_response["amount"] == round(payload["amount"], 4)
    assert json_response["description"] == payload["description"]

    response = client.get(f"/customers/wallets/{wallet_id}").json()
    assert response["balance"] == round(payload["amount"], 4)


def test_try_to_deposit_in_a_non_existent_wallet(client):
    wallet_id = str(uuid4())
    payload = {"amount": 500, "description": "Bad entry"}

    response = client.post(f"/customers/wallets/{wallet_id}/deposit", json=payload)

    with pytest.raises(HTTPError):
        response.raise_for_status()

    assert response.status_code == 404


def test_try_to_deposit_negative_amount(client, customer_wallet):
    wallet_id = str(customer_wallet.id)
    payload = {"amount": -500, "description": "Bad entry"}

    response = client.post(f"/customers/wallets/{wallet_id}/deposit", json=payload)

    with pytest.raises(HTTPError):
        response.raise_for_status()

    assert response.status_code == 409

    response = client.get(f"/customers/wallets/{wallet_id}").json()
    assert response["balance"] == 0
