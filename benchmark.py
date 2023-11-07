import numpy as np
import time
import sys

import pycuda.autoinit
import pycuda.driver as cuda
from pycuda.compiler import SourceModule

mod = SourceModule(open("sha256.cu", "r").read())

sha256_cuda = mod.get_function("sha256_cuda")

count = 0
min_value = np.zeros(32, dtype=np.uint8)
results = np.zeros(65536, dtype=np.uint8)

start_time = time.time()

while True:
    prefix = np.frombuffer(count.to_bytes(65 + 30, byteorder="big"), dtype=np.uint8)

    sha256_cuda(
        cuda.In(prefix),
        np.uint32(prefix.size),
        cuda.In(min_value),
        cuda.Out(results),
        block=(256, 1, 1),
        grid=(256, 1)
    )

    if time.time() - start_time >= 60:
        break

    count = count + 1

print(f"Hashrate: {count * 65536 / 60 / 1000 / 1000} MH/s", file=sys.stderr)
