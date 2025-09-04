#!/bin/bash
set -e

WORKING_DIR='/home/ec2-user/python-nectar-module'
CREDENTIALS_DIR='/home/ec2-user/tamarin-credentials/json'
MOUNT_FOLDER=/home/ec2-user/nectarpy-mount

# Function to display usage/help
function show_help {
    echo -e "\e[31mInvalid arguments.\e[0m"
    echo -e "\e[32mUsage: $0 build|run|debug da|do\e[0m"
}

# Function to print a step message
function print_step {
    echo -e "\e[32m=> $1\e[0m"
}

# Ensure the script is executed from the expected working directory
if [ "$WORKING_DIR" != "$(pwd)" ]; then
    echo "Please run this script from $WORKING_DIR directory!"
    echo "E.g.: cd $WORKING_DIR && ./script/nectapy.sh"
    exit 1
fi

# Check that exactly two or three arguments are provided
if [ "$#" -ne 2 ] && [ "$#" -ne 3 ]; then
    show_help
    exit 1
fi

ACTION="$1"
MODE="$2"

# Validate the action argument
case "$ACTION" in
    build|run|debug) ;;
    *) show_help; exit 1 ;;
esac

# Validate the mode argument
case "$MODE" in
    da|do) ;;
    *) show_help; exit 1 ;;
esac

# Set container and image names based on the mode
CONTAINER_NAME="nectapy-$MODE"
IMAGE_NAME="nectapy-$MODE"

# Set port mapping based on mode
if [ "$MODE" = "da" ]; then
    HOST_PORT=8888
else
    HOST_PORT=8889
fi

case "$ACTION" in
    build)
        print_step "Copying credentials to nectarpy config..."
        rm -rf ./nectarpy/config/*
        cp "$CREDENTIALS_DIR"/*.json ./nectarpy/config/
        print_step "Building Docker image ($IMAGE_NAME)..."
        # Assuming your Dockerfile names follow the pattern Dockerfile.DA or Dockerfile.DO
        docker build -f "./docker/aws/Dockerfile.$(echo $MODE | tr '[:lower:]' '[:upper:]')" -t "$IMAGE_NAME" .
        ;;
    run)
        FULL_MOUNT_FOLDER=$(echo "$MOUNT_FOLDER/$MODE" | tr '[:upper:]' '[:lower:]')
        # If the params is force like "run da/do force", then remove the mount folder
        if [ "$#" -eq 3 ] && [ "$3" = "--force" ]; then
            print_step "Removing existing mount folder ($FULL_MOUNT_FOLDER)..."
            rm -rf "$FULL_MOUNT_FOLDER"
        fi
        # Create mount folder if it doesn't exist (lower case)
        echo "Full mount folder: $FULL_MOUNT_FOLDER"
        if [ ! -d "$FULL_MOUNT_FOLDER" ]; then
            print_step "Creating mount folder ($MOUNT_FOLDER)..."
            mkdir -p "$FULL_MOUNT_FOLDER"
        fi
        print_step "Changing permissions of mount folder ($FULL_MOUNT_FOLDER)..."
        chmod 777 -R "$FULL_MOUNT_FOLDER"

        print_step "Removing existing container ($CONTAINER_NAME) if it exists..."
        docker rm -f "$CONTAINER_NAME" || true
        print_step "Starting container ($CONTAINER_NAME) with host port $HOST_PORT..."
        docker run --restart always -d \
                   -p ${HOST_PORT}:9000 \
                   --name "$CONTAINER_NAME" \
                   -v "$FULL_MOUNT_FOLDER":/app/main/sample \
                   "$IMAGE_NAME"
        print_step "Container started."
        print_step "Mounted folder: $FULL_MOUNT_FOLDER"
        ;;
    debug)
        docker logs -f "$CONTAINER_NAME" --tail 150
        ;;
esac
