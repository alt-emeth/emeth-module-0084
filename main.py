import argparse
import hashlib
import json
import numpy as np
import os
import sys
import time

is_cuda = False

try:
    import pycuda.autoinit
    import pycuda.driver as cuda
    from pycuda.compiler import SourceModule

    is_cuda = cuda.Device.count() > 0

except ImportError:
    None

parser = argparse.ArgumentParser(usage="%(prog)s [options] job_id input_dir_or_file output_dir_or_file")
parser.add_argument("--dataset-type", dest="dataset_type")
args, remain = parser.parse_known_args()

if len(remain) < 3:
    parser.print_help()
    sys.exit(1)

job_id, input_dir_or_file, output_dir_or_file = remain[-3], remain[-2], remain[-1]

errors = []

if args.dataset_type == 'direct':
    input_file = input_dir_or_file
else:
    input_file = os.path.join(input_dir_or_file, f'input-{job_id}.dat')

with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

input = lines[0]

if len(input) != 194:
    errors.append(f"{input_file}#L1: Invalid input length.")

if not len(errors):
    input_bytes = bytes.fromhex(input)

    challenge = input_bytes[0:65]
    min_value = input_bytes[65:]

    nonce = 0

    if is_cuda:
        mod = SourceModule(open("sha256.cu", "r").read())

        sha256_cuda = mod.get_function("sha256_cuda")

        results = np.zeros(65536, dtype=np.uint8)

        start_time = time.time()
        count = 0

        base = 0
        while True:
            prefix = np.frombuffer(
                challenge + base.to_bytes(30, byteorder="big"), dtype=np.uint8)

            sha256_cuda(
                cuda.In(prefix),
                np.uint32(prefix.size),
                cuda.In(np.frombuffer(min_value)),
                cuda.Out(results),
                block=(256, 1, 1),
                grid=(256, 1)
            )

            found = np.where(results == 1)[0]
            if found.size > 0:
                nonce = base * 65536 + found[0].item()
                break

            base = base + 1

            count += 1
            if time.time() - start_time >= 60:
                print(f"Hashrate: {count * 65536 / 60 / 1000 / 1000} MH/s")

                start_time = time.time()
                count = 0

    else:
        print("Warning: No CUDA device has been detected, fallback to CPU-based routine...", file=sys.stderr)

        start_time = time.time()
        count = 0

        challenge_hash = hashlib.sha256(challenge)
        while True:
            hash = challenge_hash.copy()
            hash.update(nonce.to_bytes(32, byteorder='big'))

            hash_result = hash.digest()

            if hash_result <= min_value:
                break

            nonce += 1

            count += 1
            if time.time() - start_time >= 60:
                print(f"Hashrate: {count / 60 / 1000 / 1000} MH/s")

                start_time = time.time()
                count = 0

    if args.dataset_type == 'direct':
        output_file = output_dir_or_file
    else:
        output_file = os.path.join(output_dir_or_file, f'output-{job_id}.dat')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f'{(challenge + nonce.to_bytes(32, byteorder="big")).hex()}\n')

if len(errors) > 0:
    if args.dataset_type == 'direct':
        for error in errors:
            print(error, file=sys.stderr)

        sys.exit(1)
    else:
        errors_file = os.path.join(output_dir_or_file, 'error.json')

        with open(errors_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps({"errors": errors}))
