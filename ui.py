# app.py
import os
import asyncio
import streamlit as st

from aptos_sdk.account import Account
from aptos_sdk.async_client import RestClient
from aptos_sdk.transactions import EntryFunction, TransactionPayload, TransactionArgument
from aptos_sdk.bcs import Serializer

# =====================
# CONFIG
# =====================
NODE_URL = "https://fullnode.testnet.aptoslabs.com/v1"
MODULE_ADDRESS = "0x1c6d89ac6b57c23e07ce431ea4e54ad340965d29aa4278c5767b211776361fc3"
CLIENT = RestClient(NODE_URL)

# =====================
# PAGE
# =====================
st.set_page_config(
    page_title="SecurePool | MicroInsurance DApp",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================
# HELPERS
# =====================

def create_account():
    """Create a new Aptos account and store it in session state."""
    try:
        private_key_hex = os.urandom(32).hex()
        account = Account.load_key(private_key_hex)
        st.session_state["account"] = account
        st.success(f"✅ Demo account created.\n\nAddress: {account.address()}")
        return account
    except Exception as e:
        st.error(f"❌ Failed to create account: {e}")
        return None


def get_account():
    return st.session_state.get("account", None)


async def _submit_entry_function(account: Account, module_addr: str, module_name: str,
                                 func_name: str, args: list):
    """
    Build -> sign -> submit -> wait for an entry function transaction.
    Works with aptos_sdk Python package.
    """
    try:
        entry_func = EntryFunction.natural(
            f"{module_addr}::{module_name}",
            func_name,
            [],
            args,
        )
        payload = TransactionPayload(entry_func)

        # ✅ FIXED: directly build signed txn
        signed_txn = CLIENT.create_bcs_transaction(account, payload)

        # ✅ Submit
        tx_hash = CLIENT.submit_bcs_transaction(signed_txn)

        # ✅ Wait
        CLIENT.wait_for_transaction(tx_hash)

        return tx_hash
    except Exception as e:
        raise RuntimeError(f"Transaction failed: {e}")


        return tx_hash
    except Exception as e:
        raise RuntimeError(f"Transaction failed: {e}")


# ----- App actions (async) -----

async def publish_pool_async(name: str, premium: int, coverage: int):
    account = get_account()
    if not account:
        st.warning("⚠ Please create or load an account first!")
        return False
    try:
        args = [
            TransactionArgument(name, Serializer.str),
            TransactionArgument(premium, Serializer.u64),
            TransactionArgument(coverage, Serializer.u64),
        ]
        await _submit_entry_function(
            account,
            MODULE_ADDRESS,
            "MicroInsurance",
            "create_pool",
            args,
        )
        st.success("🎉 Pool created successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Failed to create pool: {str(e)}")
        return False


async def join_pool_async(pool_id: int):
    account = get_account()
    if not account:
        st.warning("⚠ Please create or load an account first.")
        return False
    try:
        args = [TransactionArgument(pool_id, Serializer.u64)]
        await _submit_entry_function(
            account,
            MODULE_ADDRESS,
            "MicroInsurance",
            "join_pool",
            args,
        )
        st.success(f"✅ Joined pool #{pool_id} successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Failed to join pool: {e}")
        return False


async def submit_claim_async(pool_id: int, amount: int, description: str):
    account = get_account()
    if not account:
        st.warning("⚠ Please create or load an account first.")
        return False
    try:
        args = [
            TransactionArgument(pool_id, Serializer.u64),
            TransactionArgument(amount, Serializer.u64),
            TransactionArgument(description, Serializer.str),
        ]
        await _submit_entry_function(
            account,
            MODULE_ADDRESS,
            "MicroInsurance",
            "submit_claim",
            args,
        )
        st.success(f"📩 Claim submitted for pool #{pool_id}!")
        return True
    except Exception as e:
        st.error(f"❌ Failed to submit claim: {e}")
        return False


async def vote_claim_async(claim_id: int, approve: bool):
    account = get_account()
    if not account:
        st.warning("⚠ Please create or load an account first.")
        return False
    try:
        args = [
            TransactionArgument(claim_id, Serializer.u64),
            TransactionArgument(approve, Serializer.bool),
        ]
        await _submit_entry_function(
            account,
            MODULE_ADDRESS,
            "MicroInsurance",
            "vote_on_claim",
            args,
        )
        st.success(f"🗳 Voted {'Approve' if approve else 'Reject'} on claim #{claim_id}.")
        return True
    except Exception as e:
        st.error(f"❌ Failed to vote on claim: {e}")
        return False


# ----- Sync wrappers for Streamlit buttons -----

def publish_pool(name: str, premium: int, coverage: int):
    return asyncio.run(publish_pool_async(name, premium, coverage))


def join_pool(pool_id: int):
    return asyncio.run(join_pool_async(pool_id))


def submit_claim(pool_id: int, amount: int, description: str):
    return asyncio.run(submit_claim_async(pool_id, amount, description))


def vote_claim(claim_id: int, approve: bool):
    return asyncio.run(vote_claim_async(claim_id, approve))


# =====================
# UI
# =====================

st.markdown("<h1>🛡 SecurePool</h1>", unsafe_allow_html=True)
st.caption("Decentralized MicroInsurance Platform on Aptos")

acct = get_account()
if acct:
    st.info(f"🔐 Active Account: {acct.address()}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("👤 Account")
    if not acct:
        if st.button("Create Demo Account"):
            create_account()
    else:
        st.success("Account ready. You can create and join pools.")

    st.markdown("---")
    st.subheader("🏗 Create Pool")
    pool_name = st.text_input("Pool Name", placeholder="e.g., Auto Insurance Pool")
    c1, c2 = st.columns(2)
    with c1:
        premium_amount = st.number_input("Premium (Octas)", min_value=1, value=100)
    with c2:
        coverage_amount = st.number_input("Coverage (Octas)", min_value=1, value=1000)

    if st.button("🚀 Create Pool"):
        if pool_name.strip():
            publish_pool(pool_name, premium_amount, coverage_amount)
        else:
            st.warning("⚠ Please enter a pool name.")

with col2:
    st.subheader("🤝 Join Pool")
    join_pool_id = st.number_input("Pool ID to Join", min_value=1, value=1)
    if st.button("Join Pool"):
        join_pool(join_pool_id)

st.markdown("---")

c3, c4 = st.columns(2)
with c3:
    st.subheader("📝 Submit Claim")
    claim_pool_id = st.number_input("Pool ID for Claim", min_value=1, value=1)
    claim_amount = st.number_input("Claim Amount (Octas)", min_value=1, value=100)
    claim_desc = st.text_area("Claim Description", placeholder="Describe your claim...")
    if st.button("Submit Claim"):
        if claim_desc.strip():
            submit_claim(claim_pool_id, claim_amount, claim_desc)
        else:
            st.warning("⚠ Please provide a claim description.")

with c4:
    st.subheader("📊 Vote on Claims")
    vote_claim_id = st.number_input("Claim ID", min_value=1, value=1)
    vote_choice = st.radio("Your Vote", ["✅ Approve", "❌ Reject"], index=0)
    if st.button("Cast Vote"):
        approve_bool = vote_choice.startswith("✅")
        vote_claim(vote_claim_id, approve_bool)

st.markdown("---")
st.caption("Built on Aptos • Powered by Move • Testnet")
