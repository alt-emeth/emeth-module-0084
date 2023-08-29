"use strict";

const fs = require('fs');
const crypto = require('crypto');
const path = require('path');

const [jobId, inputDir, outputDir] = process.argv.slice(2);

const raw = fs.readFileSync(path.join(inputDir, `input-${jobId}.dat`), 'utf8');
const dataset = raw.split(/\r\n|\n/);

const data = dataset[0].split(/,/);
const challenge = Buffer.from(data[0].slice(2), 'hex');
const minValue = Buffer.from(data[1].slice(2), 'hex');

let nonce = 0n;

while (true) {
  const hash = crypto
    .createHash('sha256')
    .update(challenge)
    .update(Buffer.from(nonce.toString(16).padStart(64, '0'), 'hex'))
    .digest();

  if (hash.compare(minValue) <= 0) {
    break;
  }

  nonce++
}

fs.appendFileSync(
  path.join(outputDir, `output-${jobId}.dat`),
  `${nonce}\n`,
  'utf-8'
);
