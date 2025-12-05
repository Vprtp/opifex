#!/bin/bash

# Fail on error, unset vars, and catch pipeline errors
set -euo pipefail

############################################
# USER CONFIGURATION
############################################

# Whether to enforce the 10GB free-tier limit.
# Set to "true" to enable the size check, "false" to skip it.
ENFORCE_FREE_TIER=true

# Max free-tier size in bytes (10GB)
MAX_SIZE_BYTES=$((10 * 1024 * 1024 * 1024))

############################################
# PATH CONFIGURATION
############################################

SOURCE_DIR="../source"
ARCHIVE_NAME="source.tar.gz"

############################################
# LOAD CREDENTIALS
############################################

if [[ ! -f "./r2_credentials.env" ]]; then
    echo "ERROR: r2_credentials.env not found!"
    exit 1
fi
source ./r2_credentials.env

############################################
# CHECK SOURCE FOLDER
############################################

if [[ ! -d "$SOURCE_DIR" ]]; then
    echo "ERROR: Source directory '$SOURCE_DIR' does not exist."
    exit 1
fi

############################################
# OPTIONAL FREE-TIER 10GB CHECK
############################################

if [[ "$ENFORCE_FREE_TIER" = true ]]; then
    echo "Checking folder size to enforce 10GB free-tier limit..."

    # 'du -sb' = bytes, GNU-compatible. macOS uses -sk → handled below.
    if du -sb "$SOURCE_DIR" >/dev/null 2>&1; then
        DIR_SIZE_BYTES=$(du -sb "$SOURCE_DIR" | cut -f1)
    else
        # macOS fallback (du -sk gives KiB)
        DIR_SIZE_KB=$(du -sk "$SOURCE_DIR" | cut -f1)
        DIR_SIZE_BYTES=$((DIR_SIZE_KB * 1024))
    fi

    echo "Folder size: $DIR_SIZE_BYTES bytes"

    if (( DIR_SIZE_BYTES > MAX_SIZE_BYTES )); then
        echo "ERROR: Directory exceeds 10GB free-tier limit."
        echo "Size: $DIR_SIZE_BYTES bytes"
        echo "Limit: $MAX_SIZE_BYTES bytes"
        exit 1
    fi

    echo "Folder is within free-tier limit."
fi

############################################
# CREATE ARCHIVE
############################################

echo "Packing files into archive..."
tar -czf "$ARCHIVE_NAME" -C "$SOURCE_DIR" .

############################################
# CHECK FOR AWS CLI
############################################

if ! command -v aws >/dev/null 2>&1; then
    echo "AWS CLI not found. Please install it:"
    echo "  Linux: sudo apt install awscli"
    echo "  Mac:   brew install awscli"
    exit 1
fi

############################################
# CONFIGURE AWS CLI FOR CLOUDFLARE R2
############################################

aws configure set default.s3.signature_version s3v4
aws configure set aws_access_key_id "$R2_ACCESS_KEY_ID"
aws configure set aws_secret_access_key "$R2_SECRET_ACCESS_KEY"

R2_ENDPOINT="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

############################################
# UPLOAD TO R2
############################################

echo "Uploading to Cloudflare R2..."

aws s3 cp "$ARCHIVE_NAME" \
    "s3://${R2_BUCKET}/${R2_OBJECT}" \
    --endpoint-url "$R2_ENDPOINT"

echo "Upload complete!"

############################################
# CLEANUP
############################################

rm -f "$ARCHIVE_NAME"
echo "Removed temporary archive."

echo "Done!"

