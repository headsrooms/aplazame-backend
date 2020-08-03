def test_get_transactions(
    client,
    random_customer,
    customer_wallet,
    ten_deposit_transactions_in_a_wallet,
    ten_debit_transactions_in_a_wallet,
):
    received_wallets = client.get(
        f"/customers/{str(random_customer.id)}/transactions"
    ).json()["wallets"]

    assert received_wallets[0]["id"] == str(customer_wallet.id)

    all_transactions = (
        ten_deposit_transactions_in_a_wallet + ten_debit_transactions_in_a_wallet
    )
    all_transactions_ids = [str(transaction.id) for transaction in all_transactions]
    received_transactions_ids = [
        transaction["id"]
        for wallet in received_wallets
        for transaction in wallet["transactions"]
    ]
    assert all(
        [
            transaction_id in all_transactions_ids
            for transaction_id in received_transactions_ids
        ]
    )


def test_get_customer_wallet_transactions(
    client,
    customer_wallet,
    ten_deposit_transactions_in_a_wallet,
    ten_debit_transactions_in_a_wallet,
):
    received_transactions = client.get(
        f"/customers/wallets/{str(customer_wallet.id)}/transactions"
    ).json()["transactions"]


    all_transactions = (
        ten_deposit_transactions_in_a_wallet + ten_debit_transactions_in_a_wallet
    )
    all_transactions_ids = [str(transaction.id) for transaction in all_transactions]
    received_transactions_ids = [
        transaction["id"]
        for transaction in received_transactions
    ]
    assert all(
        [
            transaction_id in all_transactions_ids
            for transaction_id in received_transactions_ids
        ]
    )
