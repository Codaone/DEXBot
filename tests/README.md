Overview
========

This testsuite is based on [pytest](https://docs.pytest.org/en/latest/contents.html)

Testsuite wants to run local bitshares-core testnet via docker containter. This implies the following requirements are
satisfied:

* Your platform supports docker
* docker daemon is installed and configured
* current user is able to interact with docker daemon and have sufficient permissions

Running testsuite
-----------------

```
pip install -r requirements-dev.txt
```

Run all tests:

```
pytest
```

or

```
python -m pytest
```

Run single test:

```
pytest tests/test_prepared_testnet.py
```

How to prepare genesis.json
---------------------------

genesis.json contains initial accounts including witnesses and committee members. Every account has it's public key.
For the sake of simplicity, pick any keypair and use it's public key for every account.

Balances
--------

At the beginning, all balances are stored in `initial_balances` object. To access these balances, users must claim them
via `balance_claim` operation. This step is automated.

`initial_balances` object has `owner` field which is graphene Address. To generate an address from public key, use the
following code:

```python
from graphenebase import PublicKey, Address

w = '5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3'
k = PublicKey.from_privkey(w)
a = Address.from_pubkey(k)
str(a)
```
