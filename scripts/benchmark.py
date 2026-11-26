"""Measure salted SHA-256 hashes per second on this machine (Section 4.2)."""
import hashlib
import os
import secrets
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def benchmark(n: int = 1_000_000) -> float:
    salt = secrets.token_hex(16)
    words = [f"candidate{i}" for i in range(1000)]
    t0 = time.perf_counter()
    done = 0
    while done < n:
        for w in words:
            hashlib.sha256((w + salt).encode("utf-8")).hexdigest()
            done += 1
            if done >= n:
                break
    elapsed = time.perf_counter() - t0
    rate = n / elapsed if elapsed > 0 else 0
    return rate


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
    rate = benchmark(count)
    print(f"Salted SHA-256: {rate:,.0f} hashes per second ({count:,} hashes)")
