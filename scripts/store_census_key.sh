4#!/bin/bash
# Store Census API key in macOS Keychain (safest option)
#
# This script stores your Census Bureau API key in the encrypted macOS Keychain.
# Benefits:
#   - Key is encrypted at rest by the OS
#   - Cannot accidentally be committed to git
#   - Persists across terminal sessions
#   - Accessible only to your user account
#
# Usage:
#   ./scripts/store_census_key.sh
#
# To verify it's stored:
#   security find-generic-password -s TOXMAP_CENSUS_API_KEY -w
#
# To delete:
#   security delete-generic-password -s TOXMAP_CENSUS_API_KEY

set -e

# Check if we're on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: This script only works on macOS."
    echo "On Linux, use: export CENSUS_API_KEY=your_key"
    exit 1
fi

# Prompt for the key (hidden input)
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Census Bureau API Key Storage (macOS Keychain)              ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Get a free key: https://api.census.gov/data/key_signup.html ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo -n "Enter your Census API key: "
read -s CENSUS_KEY
echo ""

# Validate input
if [[ -z "$CENSUS_KEY" ]]; then
    echo "Error: No key provided."
    exit 1
fi

# Check if key already exists and delete if so
if security find-generic-password -s TOXMAP_CENSUS_API_KEY -a "$USER" >/dev/null 2>&1; then
    echo "Updating existing key in Keychain..."
    security delete-generic-password -s TOXMAP_CENSUS_API_KEY -a "$USER" >/dev/null 2>&1
fi

# Store in Keychain
security add-generic-password \
    -s TOXMAP_CENSUS_API_KEY \
    -a "$USER" \
    -w "$CENSUS_KEY" \
    -T "" \
    -U

echo ""
echo "✅ Census API key stored in macOS Keychain."
echo ""
echo "To use it:"
echo "  cd backend"
echo "  python -m ingestion.census_ingest --year 2020 --state VA"
echo ""
echo "The ingestion script will automatically retrieve the key from Keychain."
