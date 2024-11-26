#!/bin/bash

echo "Running the script, here goes something..."
# Check the argument passed to the Docker container
if [ "$1" = "autopilot_client" ]; then
    # Run autopilot_client.py if "autopilot" is passed
    python autopilot_client.py
elif [ "$1" = "base_station_client" ]; then
    # Run base_station_client.py if "base_station" is passed
    python base_station_client.py
else
    echo "Invalid argument. Please specify 'autopilot' or 'base_station'."
    exit 1
fi