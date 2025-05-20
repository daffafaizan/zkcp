#!/bin/bash

echo "Stopping Bitcoin Core..."
bitcoin-cli -regtest stop

echo "Removing regtest directory..."
rm -rf ~/Library/Application\ Support/Bitcoin/regtest

echo "Reset complete."