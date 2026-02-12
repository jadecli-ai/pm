#!/bin/bash
# Meta Ads → Google Sheets Sync
#
# Simple wrapper for non-technical users. Just run:
#   ./sync-ads.sh
#
# Requires .env file with META_CAMPAIGN_ID and GOOGLE_SHEET_ID set.
# See env.template for all required variables.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables
if [[ -f .env ]]; then
    source .env
else
    echo "ERROR: .env file not found"
    echo "Copy env.template to .env and fill in your credentials"
    exit 1
fi

# Check required variables
if [[ -z "${META_CAMPAIGN_ID}" ]]; then
    echo "ERROR: META_CAMPAIGN_ID not set in .env"
    exit 1
fi

if [[ -z "${GOOGLE_SHEET_ID}" ]]; then
    echo "ERROR: GOOGLE_SHEET_ID not set in .env"
    exit 1
fi

# Run the sync
python -m lib.cli \
    --campaign "${META_CAMPAIGN_ID}" \
    --sheet "${GOOGLE_SHEET_ID}" \
    "$@"
