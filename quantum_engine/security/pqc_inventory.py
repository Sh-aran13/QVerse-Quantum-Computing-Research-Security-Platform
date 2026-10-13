"""
Post-Quantum Cryptography (PQC) Migration Assessment Engine
Categorizes cryptographic algorithms against Shor's & Grover's attacks,
identifies Harvest-Now-Decrypt-Later (HNDL) risks, and provides NIST PQC migration paths.
"""

from typing import Dict, Any, List

# Authoritative NIST PQC Classification Dataset (Version 1.0)
ALGORITHM_TAXONOMY = {
    # Asymmetric Key Encapsulation / Key Exchange (Broken by Shor)
    "rsa": {
        "family": "Asymmetric (Integer Factorization)",
        "quantum_status": "Vulnerable (Shor's Algorithm)",
        "risk_level": "Critical",
        "hndl_risk": True,
        "migration_target": "ML-KEM (Kyber-768 / Kyber-1024)",
        "nist_standard": "FIPS 203 (ML-KEM)"
    },
    "diffie-hellman": {
        "family": "Asymmetric (Discrete Logarithm)",
        "quantum_status": "Vulnerable (Shor's Algorithm)",
        "risk_level": "Critical",
        "hndl_risk": True,
        "migration_target": "ML-KEM (Kyber-768)",
        "nist_standard": "FIPS 203 (ML-KEM)"
    },
    "ecdh": {
        "family": "Asymmetric (Elliptic Curve Discrete Log)",
        "quantum_status": "Vulnerable (Shor's Algorithm)",
        "risk_level": "Critical",
        "hndl_risk": True,
        "migration_target": "ML-KEM (Kyber-768)",
        "nist_standard": "FIPS 203 (ML-KEM)"
    },
    # Digital Signatures (Broken by Shor)
    "ecdsa": {
        "family": "Digital Signature (ECDSA)",
        "quantum_status": "Vulnerable (Shor's Algorithm)",
        "risk_level": "High",
        "hndl_risk": False,  # Signatures cannot be retroactively decrypted, only forged once Q-Day arrives
        "migration_target": "ML-DSA (Dilithium) or SLH-DSA (SPHINCS+)",
        "nist_standard": "FIPS 204 (ML-DSA) / FIPS 205 (SLH-DSA)"
    },
    "rsa-pss": {
        "family": "Digital Signature (RSA-PSS)",
        "quantum_status": "Vulnerable (Shor's Algorithm)",
        "risk_level": "High",
        "hndl_risk": False,
        "migration_target": "ML-DSA (Dilithium)",
        "nist_standard": "FIPS 204 (ML-DSA)"
    },
    # Symmetric Ciphers (Affected by Grover - Requires key doubling)
    "aes-128": {
        "family": "Symmetric Block Cipher",
        "quantum_status": "Weakened (Grover: 64-bit effective security)",
        "risk_level": "Medium",
        "hndl_risk": True,
        "migration_target": "AES-256 (128-bit quantum security)",
        "nist_standard": "NIST SP 800-175B"
    },
    "aes-256": {
        "family": "Symmetric Block Cipher",
        "quantum_status": "Quantum-Resistant (Grover: 128-bit effective security)",
        "risk_level": "Low",
        "hndl_risk": False,
        "migration_target": "Maintain AES-256",
        "nist_standard": "FIPS 197"
    },
    # Hashes (Grover / Brassard)
    "sha-256": {
        "family": "Cryptographic Hash",
        "quantum_status": "Quantum-Resistant (128-bit collision resistance)",
        "risk_level": "Low",
        "hndl_risk": False,
        "migration_target": "Maintain SHA-256 / SHA-384",
        "nist_standard": "FIPS 180-4"
    },
    "sha-3": {
        "family": "Cryptographic Hash",
        "quantum_status": "Quantum-Resistant",
        "risk_level": "Low",
        "hndl_risk": False,
        "migration_target": "Maintain SHA-3",
        "nist_standard": "FIPS 202"
    },
    # Post-Quantum Native Standards
    "ml-kem": {
        "family": "Lattice-Based KEM",
        "quantum_status": "Quantum-Safe Standard",
        "risk_level": "None",
        "hndl_risk": False,
        "migration_target": "Already Quantum-Safe",
        "nist_standard": "FIPS 203"
    },
    "ml-dsa": {
        "family": "Lattice-Based Signature",
        "quantum_status": "Quantum-Safe Standard",
        "risk_level": "None",
        "hndl_risk": False,
        "migration_target": "Already Quantum-Safe",
        "nist_standard": "FIPS 204"
    }
}

def assess_crypto_inventory(inventory_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluates an asset inventory list and generates a structured migration assessment report.
    """
    assessed_assets = []
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_or_safe = 0
    hndl_vulnerabilities = 0

    for item in inventory_items:
        system_name = item.get("system_name", "Unknown System")
        raw_algo = str(item.get("algorithm", "")).strip().lower()

        # Lookup rule
        matched_spec = None
        for key, spec in ALGORITHM_TAXONOMY.items():
            if key in raw_algo or raw_algo in key:
                matched_spec = spec
                break

        if not matched_spec:
            matched_spec = {
                "family": "Custom / Unrecognized",
                "quantum_status": "Review Required",
                "risk_level": "Review Required",
                "hndl_risk": False,
                "migration_target": "Consult NIST PQC Guidelines",
                "nist_standard": "Under Review"
            }

        risk = matched_spec["risk_level"]
        if risk == "Critical":
            critical_count += 1
        elif risk == "High":
            high_count += 1
        elif risk == "Medium":
            medium_count += 1
        else:
            low_or_safe += 1

        if matched_spec.get("hndl_risk"):
            hndl_vulnerabilities += 1

        assessed_assets.append({
            "system_name": system_name,
            "algorithm": item.get("algorithm", ""),
            "business_criticality": item.get("criticality", "Medium"),
            "family": matched_spec["family"],
            "quantum_status": matched_spec["quantum_status"],
            "risk_level": risk,
            "hndl_risk": matched_spec.get("hndl_risk", False),
            "migration_target": matched_spec["migration_target"],
            "nist_standard": matched_spec["nist_standard"]
        })

    total_assets = len(inventory_items)
    overall_posture = "Critical Migration Required" if (critical_count > 0 or hndl_vulnerabilities > 0) else (
        "Moderate Quantum Risk" if (high_count > 0 or medium_count > 0) else "Quantum Resilient"
    )

    return {
        "ruleset_version": "NIST FIPS 203/204/205 PQC v1.0",
        "total_assets": total_assets,
        "overall_posture": overall_posture,
        "critical_count": critical_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_or_safe": low_or_safe,
        "hndl_vulnerabilities": hndl_vulnerabilities,
        "assessed_assets": assessed_assets,
        "methodology": "Classified using authoritative NIST Post-Quantum Cryptography standards. Harvest-Now-Decrypt-Later flags highlight key exchanges susceptible to present-day wiretapping and future retro-decryption."
    }
