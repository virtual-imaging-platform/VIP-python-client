This is an admin-level tool to manage VIP apps descriptors.

For commands that communicate with a VIP instance, set these two
environment variables:
- `export VIP_API_URL=...`  # VIP-portal host URL (without /rest)
- `export VIP_API_KEY=...`  # Your API key (admin level required)

Then see usage with:
`python3 ./vipapps/vipapps.py --help`
or `python3 ./vipapps/vipapps.py <command> --help`
