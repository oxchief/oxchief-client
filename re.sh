#!/bin/bash

# Determine the directory of the re.sh script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source oxchief.sh using its path relative to re.sh
source "$SCRIPT_DIR/scripts/oxchief.sh"

# Call check_auth_file_exists_and_exit_if_not from oxchief.sh
check_auth_file_exists_and_exit_if_not

# Source the .oxchief file to load environment variables
source $auth_file

# Set the mode flag based on whether robot_id is defined
if [ -n "$robot_id" ]; then
    mode="robot"
else
    mode="base"
fi

# Continue with the rest of the script
echo "Mode is set to: $mode"

print_working() {
    while true; do
        echo -n "."
        sleep 1
    done
}

echo "Finding oxchief containers"
# Get the container IDs for containers with ancestor name containing "oxchief"
CONTAINER_IDS=$(docker ps -a --format "{{.ID}} {{.Image}}" | grep "oxchief" | awk '{print $1}')

# Stop and remove each container
for CONTAINER_ID in $CONTAINER_IDS; do
    echo "Stopping container $CONTAINER_ID"
    print_working &
    print_working_pid=$!
    docker stop "$CONTAINER_ID"
    kill $print_working_pid
    wait $print_working_pid 2>/dev/null
    echo "Removing container $CONTAINER_ID"
    docker rm "$CONTAINER_ID"
done

echo "All oxchief containers have been stopped and removed."

#docker kill $(docker ps -q)

# Start the OxChief autopilot and obstacle detection services if mode is "robot"
# Otherwise, start the OxChief base station service
if [ "$mode" = "robot" ]; then
    echo "Starting OxChief autopilot"
    "$SCRIPT_DIR/scripts/oxchief.sh" autopilot
    echo "Starting OxChief obstacle detection"
    "$SCRIPT_DIR/scripts/oxchief.sh" obstacles
else
    "$SCRIPT_DIR/scripts/oxchief.sh" base
fi