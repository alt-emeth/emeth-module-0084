import hashlib
import json
import os
import sys

if len(sys.argv) != 4:
    print("Usage: python main.py <job_id> <input_dir> <output_dir>")
    sys.exit(1)

job_id, input_dir, output_dir = sys.argv[1], sys.argv[2], sys.argv[3]

errors = []

input_file = os.path.join(input_dir, f'input-{job_id}.dat')

with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

input = lines[0]

if len(input) != 194:
    errors.append(f"input-{job_id}.dat#L1: Invalid input length.")

if not len(errors):
    input_bytes = bytes.fromhex(input)

    challenge = input_bytes[0:65]
    min_value = input_bytes[65:]

    nonce = 0

    challenge_hash = hashlib.sha256(challenge)
    while True:
        hash = challenge_hash.copy()
        hash.update(nonce.to_bytes(32, byteorder='big'))

        hash_result = hash.digest()

        if hash_result <= min_value:
            break

        nonce += 1

    output_file = os.path.join(output_dir, f'output-{job_id}.dat')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f'{(challenge + nonce.to_bytes(32, byteorder="big")).hex()}\n')

if len(errors) > 0:
    errors_file = os.path.join(output_dir, 'error.json')

    with open(errors_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps({"errors": errors}))
