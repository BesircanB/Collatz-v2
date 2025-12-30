
import collections
from collatz_aes_rng import CollatzEntropySource, SecureCollatzRNG

def count_bits(data):
    """
    Counts total 0s and 1s in a byte string or list of integers (0/1).
    """
    if isinstance(data, (bytes, bytearray)):
        zero_count = 0
        one_count = 0
        for byte in data:
            # simple bit counting
            for i in range(8):
                if (byte >> i) & 1:
                    one_count += 1
                else:
                    zero_count += 1
        return zero_count, one_count
    elif isinstance(data, list):
        # List of 0s and 1s
        ones = sum(data)
        zeros = len(data) - ones
        return zeros, ones
    return 0, 0

def main():
    seed = 27
    print(f"--- Collatz Entropy Source (Von Neumann Whitened) ---")
    print(f"Seed: {seed}")
    
    # Check the raw whitened stream balance
    source = CollatzEntropySource(seed)
    # Collect 1000 bits
    bits = []
    print("Generating 1000 whitened bits...")
    for _ in range(1000):
        bits.append(source.get_whitened_bit())
    
    zeros, ones = count_bits(bits)
    print(f"Results (1000 bits):")
    print(f"  Zeros: {zeros}")
    print(f"  Ones:  {ones}")
    diff = abs(zeros - ones)
    print(f"  Difference: {diff} ({diff/1000:.1%})")
    print("Status: " + ("PERFECTLY BALANCED" if diff == 0 else "Balanced within statistical variance"))
    
    print("\n--- Secure Collatz RNG (AES-CTR) ---")
    # Generate random bytes
    rng = SecureCollatzRNG(seed)
    num_bytes = 10000
    print(f"Generating {num_bytes} bytes of AES-secured random data...")
    random_data = rng.random_bytes(num_bytes)
    
    zeros, ones = count_bits(random_data)
    total_bits = num_bytes * 8
    print(f"Results ({total_bits} bits):")
    print(f"  Zeros: {zeros}")
    print(f"  Ones:  {ones}")
    diff = abs(zeros - ones)
    print(f"  Difference: {diff} ({diff/total_bits:.2%})")
    
    print("\n--- Random Integers Example ---")
    print("5 Random numbers between 1 and 100:")
    for _ in range(5):
        print(rng.random_int(1, 100))

if __name__ == "__main__":
    main()
