import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


# ---------------------------------------------------------------------------
# Account & KYC generation
# ---------------------------------------------------------------------------

def generate_accounts(
    num_accounts: int = 200, *, now: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    types = ["Savings", "Current"]
    now = now or datetime.now()
    accounts = []
    for i in range(num_accounts):
        accounts.append(
            {
                "account_id": f"ACC_{i:04d}",
                "account_type": random.choice(types),
                "creation_date": now - timedelta(days=random.randint(30, 1800)),
                "status": "Dormant" if i % 20 == 0 else "Active",
                "balance": round(random.uniform(100, 100_000), 2),
                "last_active_date": now - timedelta(days=random.randint(1, 60)),
                "last_txn_date": now - timedelta(days=random.randint(1, 30)),
            }
        )
    return accounts


def _build_mock_kyc_from_accounts(
    accounts: List[Dict[str, Any]] = None,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Build a realistic mock KYC database.

    - ~20 % of accounts are GST-registered businesses (innocence signal)
    - Account age in months is drawn from a realistic distribution (not i % 24)
    """
    if accounts is None:
        accounts = generate_accounts(1000, now=now)

    kyc: Dict[str, Dict[str, Any]] = {}
    now = now or datetime.now()
    for acc in accounts:
        acc_id = acc["account_id"]
        creation = acc.get("creation_date", now - timedelta(days=365))
        age_months = max(0, int((now - creation).days / 30))
        kyc[acc_id] = {
            "has_gst": random.random() < 0.20,          # 20 % GST-registered
            "account_age_months": age_months,
            "kyc_status": random.choice(["Verified", "Verified", "Pending"]),
        }
    return kyc


# ---------------------------------------------------------------------------
# Fraud pattern injectors
# ---------------------------------------------------------------------------

def _txn(sender: str, receiver: str, amount: float, ts: datetime, channel: str) -> Dict:
    return {
        "txn_id": str(uuid.uuid4()),
        "sender_id": sender,
        "receiver_id": receiver,
        "amount": round(amount, 2),
        "timestamp": ts,
        "channel": channel,
        "account_type": "Savings",
    }


def create_cycle_fraud(
    accounts: List[Dict[str, Any]], start_time: datetime, hops: int = 4
) -> List[Dict[str, Any]]:
    """Round-trip cycle: A→B→C→D→A, all within a few hours (velocity signal)."""
    hops = max(3, min(hops, len(accounts)))
    nodes = [a["account_id"] for a in random.sample(accounts, hops)]
    txns = []
    amount = 100_000.0
    channels = ["NEFT", "RTGS", "IMPS"]  # cross-channel switching
    current_time = start_time
    for i in range(hops):
        sender = nodes[i]
        receiver = nodes[(i + 1) % hops]
        txns.append(
            _txn(sender, receiver, amount - i * random.uniform(100, 500),
                 current_time, random.choice(channels))
        )
        current_time += timedelta(minutes=random.randint(5, 60))
    return txns


def create_smurfing_fraud(
    accounts: List[Dict[str, Any]], start_time: datetime, num_sources: int = 8
) -> List[Dict[str, Any]]:
    """High fan-in structuring: N sources → 1 target, amounts just below ₹50 000."""
    target = random.choice(accounts)["account_id"]
    pool = [a for a in accounts if a["account_id"] != target]
    sources = [a["account_id"] for a in random.sample(pool, min(num_sources, len(pool)))]
    txns = []
    current_time = start_time
    for src in sources:
        txns.append(
            _txn(src, target, random.uniform(45_000, 49_900),
                 current_time, "IMPS")
        )
        current_time += timedelta(minutes=random.randint(1, 30))
    return txns


def create_hub_and_spoke_fraud(
    accounts: List[Dict[str, Any]], start_time: datetime,
    num_spokes_in: int = 5, num_spokes_out: int = 5
) -> List[Dict[str, Any]]:
    """Mule-network hub: many spokes send to hub, hub distributes to many destinations."""
    pool = list(accounts)
    hub = random.choice(pool)["account_id"]
    remaining = [a for a in pool if a["account_id"] != hub]
    sources = [a["account_id"] for a in random.sample(remaining, min(num_spokes_in, len(remaining)))]
    remaining2 = [a for a in remaining if a["account_id"] not in sources]
    dests = [a["account_id"] for a in random.sample(remaining2, min(num_spokes_out, len(remaining2)))]
    txns = []
    current_time = start_time
    for src in sources:
        txns.append(_txn(src, hub, random.uniform(20_000, 80_000), current_time, "NEFT"))
        current_time += timedelta(minutes=random.randint(5, 20))
    for dst in dests:
        txns.append(_txn(hub, dst, random.uniform(15_000, 70_000), current_time, random.choice(["NEFT", "RTGS"])))
        current_time += timedelta(minutes=random.randint(5, 20))
    return txns


def create_pass_through_fraud(
    accounts: List[Dict[str, Any]], start_time: datetime
) -> List[Dict[str, Any]]:
    """Pass-through mule: A→mule→B, mule forwards ~all received funds immediately."""
    pool = list(accounts)
    mule, source, dest = random.sample(pool, 3)
    mule_id, src_id, dst_id = mule["account_id"], source["account_id"], dest["account_id"]
    amount = random.uniform(50_000, 200_000)
    txns = [
        _txn(src_id, mule_id, amount, start_time, "NEFT"),
        _txn(mule_id, dst_id, amount * 0.98, start_time + timedelta(minutes=random.randint(5, 60)), "IMPS"),
    ]
    return txns


def create_dormant_activation_fraud(
    accounts: List[Dict[str, Any]], start_time: datetime
) -> List[Dict[str, Any]]:
    """
    Dormant activation: inject an account that has a very old first transaction
    (9 months ago) and a burst of new transactions today.
    """
    dormant_acc = f"DORMANT_{uuid.uuid4().hex[:6].upper()}"
    counterparts = [a["account_id"] for a in random.sample(accounts, 4)]
    old_time = start_time - timedelta(days=random.randint(270, 400))  # 9–13 months ago
    txns = [
        # One old transaction to establish the account in the graph
        _txn(counterparts[0], dormant_acc, random.uniform(500, 2000), old_time, "UPI"),
    ]
    # Recent burst
    current_time = start_time
    for cp in counterparts[1:]:
        txns.append(
            _txn(dormant_acc, cp, random.uniform(30_000, 90_000), current_time, random.choice(["NEFT", "RTGS"]))
        )
        current_time += timedelta(minutes=random.randint(10, 60))
    return txns


# ---------------------------------------------------------------------------
# Background noise
# ---------------------------------------------------------------------------

def generate_background_noise(
    accounts: List[Dict[str, Any]], num_txns: int = 1000, start_time: datetime = None
) -> List[Dict[str, Any]]:
    if start_time is None:
        start_time = datetime.now() - timedelta(days=1)
    txns = []
    channels = ["UPI", "NEFT", "IMPS", "RTGS"]
    for _ in range(num_txns):
        sender = random.choice(accounts)["account_id"]
        receiver = random.choice(accounts)["account_id"]
        while receiver == sender:
            receiver = random.choice(accounts)["account_id"]
        txns.append(
            _txn(sender, receiver, random.uniform(500, 10_000),
                 start_time + timedelta(minutes=random.randint(1, 1440)),
                 random.choice(channels))
        )
    return txns


# ---------------------------------------------------------------------------
# Scenario builder
# ---------------------------------------------------------------------------

def build_mock_kyc(source: Any = 1000) -> Dict[str, Any]:
    """
    Build a realistic mock KYC database for the ContextAgent innocence discount.

    source can be:
      - int: number of synthetic accounts
      - list[dict]: concrete account records
    """
    if isinstance(source, list):
        return _build_mock_kyc_from_accounts(source)

    num_accounts = int(source)
    accounts = generate_accounts(num_accounts)
    return _build_mock_kyc_from_accounts(accounts)


def generate_scenario(
    *,
    seed: Optional[int] = None,
    base_time: Optional[datetime] = None,
    num_accounts: int = 200,
    noise_txns: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Synthetic dataset covering all five fraud patterns defined in the PRD.
    """
    if seed is not None:
        random.seed(seed)

    if base_time is None:
        base_time = datetime.now() - timedelta(hours=24)

    accounts = generate_accounts(num_accounts, now=base_time)

    txns = generate_background_noise(accounts, noise_txns, base_time)

    txns.extend(create_cycle_fraud(accounts, base_time + timedelta(hours=2)))
    txns.extend(create_smurfing_fraud(accounts, base_time + timedelta(hours=5)))
    txns.extend(create_hub_and_spoke_fraud(accounts, base_time + timedelta(hours=8)))
    txns.extend(create_pass_through_fraud(accounts, base_time + timedelta(hours=10)))
    txns.extend(create_dormant_activation_fraud(accounts, base_time + timedelta(hours=12)))

    txns.sort(key=lambda x: x["timestamp"])
    return txns
