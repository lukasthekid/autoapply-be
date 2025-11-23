#!/bin/bash
# Bash script to set up SSH tunnel for PostgreSQL database access
# This script creates an SSH tunnel from localhost:5433 to the remote database

# Default values
SSH_SERVER="${SSH_SERVER:-5.75.171.23}"
SSH_PORT="${SSH_PORT:-22}"
LOCAL_PORT="${LOCAL_PORT:-5433}"
REMOTE_PORT="${REMOTE_PORT:-5433}"
SSH_USER="${SSH_USER}"
SSH_KEY="${SSH_KEY_PATH}"

# Check if SSH user is provided
if [ -z "$SSH_USER" ]; then
    echo "Error: SSH user not provided."
    echo "Usage: SSH_USER=username SSH_KEY_PATH=/path/to/key ./setup-ssh-tunnel.sh"
    echo "Or export environment variables: SSH_USER and SSH_KEY_PATH"
    exit 1
fi

# Check if SSH key is provided
if [ -z "$SSH_KEY" ]; then
    echo "Error: SSH key path not provided."
    echo "Usage: SSH_USER=username SSH_KEY_PATH=/path/to/key ./setup-ssh-tunnel.sh"
    exit 1
fi

# Check if SSH key file exists
if [ ! -f "$SSH_KEY" ]; then
    echo "Error: SSH key file not found at: $SSH_KEY"
    exit 1
fi

# Check if port is already in use
if lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "Warning: Port $LOCAL_PORT is already in use. The tunnel might already be running."
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo "Setting up SSH tunnel..."
echo "Local port: $LOCAL_PORT"
echo "Remote server: $SSH_SERVER:$REMOTE_PORT"
echo "SSH user: $SSH_USER"
echo ""
echo "The tunnel will run in the foreground. Press Ctrl+C to stop it."
echo ""

# Start SSH tunnel
ssh -N -L ${LOCAL_PORT}:localhost:${REMOTE_PORT} -i "$SSH_KEY" -p $SSH_PORT ${SSH_USER}@${SSH_SERVER}

