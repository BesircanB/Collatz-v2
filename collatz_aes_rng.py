
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class CollatzEntropySource:
    """
    Generates a randomized bitstream using the path taken by the Collatz conjecture.
    Applies Von Neumann whitening to ensure bit balance (0s and 1s).
    """
    def __init__(self, seed_val):
        if seed_val <= 0:
            raise ValueError("Seed must be a positive integer")
        self.state = seed_val
        # To avoid getting stuck in the 4-2-1 loop, we can perturb the state randomly
        # or use a counter. Here, if we hit 1, we restart with a derived value to keep the stream going.
        self.reset_counter = 0

    def _next_collatz_bit(self):
        """
        Step the Collatz state.
        Returns:
            0 if the number was Even (Parity 0)
            1 if the number was Odd (Parity 1)
        """
        # "Odd number 1, dual (even) number zero"
        is_odd = (self.state % 2 != 0)
        
        if is_odd:
            # Odd
            bit = 1
            # Collatz rule: 3n + 1
            self.state = 3 * self.state + 1
        else:
            # Even
            bit = 0
            # Collatz rule: n / 2
            self.state = self.state // 2

        # Check for loop cycle
        if self.state == 1:
            self.reset_counter += 1
            # Perturb state to continue generating bits
            # We use a simple linear transformation to get a new seed
            self.state = (self.reset_counter * 12345 + 6789) | 1 # Ensure odd to restart dynamics

        return bit

    def get_whitened_bit(self):
        """
        Uses Von Neumann Whitening to generate a perfectly balanced bit.
        Reads pairs of bits (a, b):
        - If (0, 1) -> Returns 0
        - If (1, 0) -> Returns 1
        - If (0, 0) or (1, 1) -> Discard and retry
        """
        while True:
            b1 = self._next_collatz_bit()
            b2 = self._next_collatz_bit()

            if b1 == 0 and b2 == 1:
                return 0
            elif b1 == 1 and b2 == 0:
                return 1
            # Else (0,0) or (1,1), discard and continue loop.

    def get_bytes(self, num_bytes):
        """
        Generates num_bytes of information.
        """
        result = bytearray()
        for _ in range(num_bytes):
            byte_val = 0
            for _ in range(8):
                bit = self.get_whitened_bit()
                byte_val = (byte_val << 1) | bit
            result.append(byte_val)
        return bytes(result)

class SecureCollatzRNG:
    """
    A Secure RNG that uses the Collatz Entropy Source to seed an AES-CTR generator.
    """
    def __init__(self, seed_val: int):
        self.entropy_source = CollatzEntropySource(seed_val)
        
        # Generator Key (128-bit) and Nonce (128-bit) from the Collatz source
        # This makes the AES key dependent on the Collatz trajectory
        self.key = self.entropy_source.get_bytes(16) # AES-128
        self.nonce = self.entropy_source.get_bytes(16)
        
        # Initialize AES in Counter Mode
        backend = default_backend()
        cipher = Cipher(algorithms.AES(self.key), modes.CTR(self.nonce), backend=backend)
        self.encryptor = cipher.encryptor()

    def random_bytes(self, n: int) -> bytes:
        """
        Generates n random bytes using AES-CTR.
        We encrypt a stream of zeros to produce the keystream.
        """
        zeros = b'\x00' * n
        return self.encryptor.update(zeros)

    def random_int(self, min_val: int, max_val: int) -> int:
        """
        Helper to get a random integer in range [min_val, max_val].
        """
        range_size = max_val - min_val + 1
        byte_len = (range_size.bit_length() + 7) // 8
        
        while True:
            rand_bytes = self.random_bytes(byte_len)
            rand_int = int.from_bytes(rand_bytes, 'big')
            # Use rejection sampling to avoid bias
            if rand_int < range_size: # Approximate check, can be refined for modulo bias
                 # A simple modulo for now, assuming large entropy pool relative to range is fine for this demo
                 # But strictly, we should reject if rand_int is in the incomplete upper range block.
                 # For simplicity of this "Collatz" demo, we just take mod.
                 return min_val + (rand_int % range_size)
