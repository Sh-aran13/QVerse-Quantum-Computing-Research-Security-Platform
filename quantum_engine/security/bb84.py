"""
BB84 Quantum Key Distribution (QKD) Simulator
Implements genuine quantum state preparation, basis reconciliation, intercept-resend Eve attack,
and Quantum Bit Error Rate (QBER) calculation.
"""

import random
import time
from typing import Dict, Any, List

# Bases:
# '+' denotes Rectilinear basis (|0>, |1>)
# 'x' denotes Diagonal basis (|+> = (|0>+|1>)/sqrt(2), |-> = (|0>-|1>)/sqrt(2))

def simulate_bb84_protocol(
    num_bits: int = 64,
    eve_present: bool = False,
    sample_ratio: float = 0.5,
    seed: int = None
) -> Dict[str, Any]:
    """
    Simulates the complete BB84 protocol:
    1. Alice generates random bits and random bases ('+' or 'x').
    2. Alice prepares simulated photon polarization states.
    3. (Optional) Eve intercepts in random bases and resends.
    4. Bob chooses random measurement bases ('+' or 'x').
    5. Bob measures photons according to quantum projection laws.
    6. Alice & Bob announce bases over public authenticated channel.
    7. Sifted key is formed where bases match.
    8. Random subset of sifted key is sacrificed to calculate QBER.
    9. Remainder forms the final secret key if QBER < threshold (~11%).
    """
    if num_bits < 8 or num_bits > 512:
        raise ValueError("Number of bits must be between 8 and 512.")

    rng = random.Random(seed)
    start_time = time.perf_counter()

    # Step 1: Alice generates random bits and random bases
    alice_bits = [rng.randint(0, 1) for _ in range(num_bits)]
    alice_bases = [rng.choice(['+', 'x']) for _ in range(num_bits)]

    # Step 2 & 3: Transmission (with optional Eve intercept-resend attack)
    eve_bases = []
    eve_bits = []
    if eve_present:
        for i in range(num_bits):
            e_basis = rng.choice(['+', 'x'])
            eve_bases.append(e_basis)
            # If Eve measures in Alice's basis, she measures Alice's bit with certainty
            # If Eve measures in the wrong basis, outcome is randomized (50/50)
            if e_basis == alice_bases[i]:
                eve_bit = alice_bits[i]
            else:
                eve_bit = rng.randint(0, 1)
            eve_bits.append(eve_bit)

    # Step 4 & 5: Bob chooses bases and measures
    bob_bases = [rng.choice(['+', 'x']) for _ in range(num_bits)]
    bob_bits = []

    for i in range(num_bits):
        # State arriving at Bob
        transmitted_bit = eve_bits[i] if eve_present else alice_bits[i]
        transmitted_basis = eve_bases[i] if eve_present else alice_bases[i]

        if bob_bases[i] == transmitted_basis:
            bob_bits.append(transmitted_bit)
        else:
            # 50% projection probability when measuring in non-matching basis
            bob_bits.append(rng.randint(0, 1))

    # Step 6 & 7: Sifting (Filter indices where Alice's basis == Bob's basis)
    sifted_indices = [i for i in range(num_bits) if alice_bases[i] == bob_bases[i]]
    sifted_alice = [alice_bits[i] for i in sifted_indices]
    sifted_bob = [bob_bits[i] for i in sifted_indices]

    sifted_len = len(sifted_indices)

    # Step 8: QBER Calculation via sacrificed sample subset
    sample_size = max(1, int(sifted_len * sample_ratio))
    sample_indices = rng.sample(range(sifted_len), min(sample_size, sifted_len)) if sifted_len > 0 else []

    errors = 0
    for idx in sample_indices:
        if sifted_alice[idx] != sifted_bob[idx]:
            errors += 1

    qber = (errors / sample_size) if sample_size > 0 else 0.0

    # Step 9: Remaining key forms final secret key
    remaining_indices = [idx for idx in range(sifted_len) if idx not in set(sample_indices)]
    final_alice_key = [sifted_alice[idx] for idx in remaining_indices]
    final_bob_key = [sifted_bob[idx] for idx in remaining_indices]

    # Security Threshold for BB84 under intercept-resend is typically ~11% (0.11)
    is_secure = (qber < 0.11) and not (eve_present and qber > 0.11)

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "num_bits_sent": num_bits,
        "eve_present": eve_present,
        "sifted_key_length": sifted_len,
        "sifted_fraction": round(sifted_len / num_bits, 3),
        "sample_size": sample_size,
        "errors_detected": errors,
        "qber": round(qber, 4),
        "qber_percentage": round(qber * 100, 2),
        "theoretical_expected_qber": 0.25 if eve_present else 0.0,
        "security_threshold": 0.11,
        "is_secure": is_secure,
        "final_key_length": len(final_alice_key),
        "execution_time_ms": duration_ms,
        # Truncated sample inspection for research visualization (first 16 bits)
        "sample_transmission": [
            {
                "index": i,
                "alice_bit": alice_bits[i],
                "alice_basis": alice_bases[i],
                "bob_basis": bob_bases[i],
                "bob_bit": bob_bits[i],
                "matched_basis": alice_bases[i] == bob_bases[i],
                "eve_intercepted": eve_present
            } for i in range(min(16, num_bits))
        ]
    }
