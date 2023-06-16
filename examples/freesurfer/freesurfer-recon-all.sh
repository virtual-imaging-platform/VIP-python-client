#!/bin/bash

python3 ../vip-cli.py \
    --session reconall-example \
    --input $(realpath ./inputs) \
    --pipeline "Freesurfer (recon-all)/0.3.8" \
    --arguments freesurfer-args.json \
    --api-key VIP_API_TOKEN
