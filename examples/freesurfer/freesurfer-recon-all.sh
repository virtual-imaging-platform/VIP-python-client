#!/bin/bash

python3 ./vip-cli.py \
    --session reconall-example \
    --input $(realpath ./inputs) \
    --pipeline "Freesurfer-Recon-all/7.3.1" \
    --arguments freesurfer-args.json \
    --api-key VIP_API_TOKEN
