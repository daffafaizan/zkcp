#!/bin/bash

echo "Stopping Bitcoin Core..."
bitcoin-cli -regtest stop

echo "Removing regtest directory..."
rm -rf ~/.bitcoin/regtest

echo "Reset complete."