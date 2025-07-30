#!/bin/bash
set -e

WORKING_DIR='/work/python-nectar-module'
CREDENTIALS_DIR='/work/authen-files/backend-api'

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

# Check that exactly two arguments are provided
if [ "$#" -ne 2 ]; then
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
        print_step "Removing existing container ($CONTAINER_NAME) if it exists..."
        docker rm -f "$CONTAINER_NAME" || true
        print_step "Starting container ($CONTAINER_NAME) with host port $HOST_PORT..."
        docker run --restart always -d -p ${HOST_PORT}:9000 --name "$CONTAINER_NAME" "$IMAGE_NAME"
        print_step "Container started."
        ;;
    debug)
        docker logs -f "$CONTAINER_NAME" --tail 150
        ;;
esac
