# `ZKCP`

### Prerequisites

You'll need Bitcoind and Bitcoin-cli to start.

For MacOS, run `brew install bitcoin`

### Steps

1. Create a new Python virtual-environment, `python -m venv env`
2. Enter environment, `source env/bin/activate`
3. Run `./zkcp_complete.sh` for ZKCP with timelock and `./zkcp_no_timelock.sh` for none.

To restart, run `./reset.sh` first.

### Notes

- `common`: common functions and commands
- `complete`: full ZKCP protocol (includes timelock)
- `no-timelock`: ZKCP protocol without timelock check
- `try`: personal trial and error bitcoin regtest directory