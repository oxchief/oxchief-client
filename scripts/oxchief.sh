#!/bin/bash

# Version of this script
VERSION="1.0.0"

# Docker image versions
DOCKER_OX_CLIENT_VERSION="1.0.2"
DOCKER_REALSENSE_VERSION="1.0.1"

project_path="$(dirname "${BASH_SOURCE[0]}")/.." # this is the path to the oxchief-client directory
# Get the path to the .oxchief authentication file in the directory below
auth_file="$project_path/../.oxchief"

#this used to be just $(pwd), but I was having an issue where, when we issue the 
#./re.sh command from within the base-station-client container (i.e. when 
#base_station_client.py tries to restart itself because it thinks it 
#needs to because of a problem), then $(pwd) wasn't mapping 
#to this directory

#project_path="/home/pi/src/oxchief/oxchief-client"

# ^^^^ Test to see if so
echo "project_path: $project_path"

container_mode=""
extra_stuff=""

# This function searches for USB devices connected to the system and prints the corresponding device names.
# It iterates through each USB device found in the /sys/bus/usb/devices/ directory.
# For each device, it retrieves the device name and other properties using udevadm.
# If the device has either the ID_USB_SERIAL or ID_SERIAL property, it prints the corresponding device name.
# The device names are printed to the console.
list_usb_names() 
{
    #List the names of all USB devices connected to the system
    for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do
        (
        syspath="${sysdevpath%/dev}"
        #echo "syspath: $syspath"
        devname="$(udevadm info -q name -p $syspath)"
        #echo "devname: $devname"

        # Skip devices that have a device name starting with "bus/"
        [[ "$devname" == "bus/"* ]] && exit

        eval "$(udevadm info -q property --export -p $syspath)"
        
        # Check if the device has either the ID_USB_SERIAL or ID_SERIAL property
        if [[ -n "$ID_USB_SERIAL" ]];then
            echo "/dev/$devname"
        elif [[ -n "$ID_SERIAL"  ]]; then
            echo "/dev/$devname"
        fi
        )
    done
}

# This function is used to find USB devices connected to the system and display their corresponding device names and serial numbers.
# It iterates through the /sys/bus/usb/devices/ directory and retrieves information about each USB device using udevadm.
# The function checks if the device has an ID_USB_SERIAL or ID_SERIAL property, and if so, it prints the device name and serial number.
# The output is displayed in the format "/dev/{device name} - {serial number}".
list_usb_info() 
{
    for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do
        (
            syspath="${sysdevpath%/dev}"
            devname="$(udevadm info -q name -p $syspath)"
            [[ "$devname" == "bus/"* ]] && exit
            eval "$(udevadm info -q property --export -p $syspath)"
            if [[ -n "$ID_USB_SERIAL" ]];then
                echo "/dev/$devname - $ID_USB_SERIAL"
            elif [[ -n "$ID_SERIAL"  ]]; then
                echo "/dev/$devname - $ID_SERIAL"
            fi
        )
    done
}

delete_all_files_in_temp_folder() 
{
    # Delete all files in the temp folder
    rm -rf "$project_path/temp"/*
    echo "All files in the temp folder deleted."
}

delete_file_if_exists()
{
    local file="$1"

    # Check if the file exists
    if [ -f "$file" ]; then
        # If the file exists, delete it
        rm -f "$file"
        echo "File '$file' deleted."
    #else
    #    echo "File '$file' does not exist."
    fi
}

restore_usb_access()
{
    # for some reason, we lose usb access from the Pi
    # to the u-blox ZED-F9P on every restart -- this
    # chmod fixes that
    sudo chmod -R 777 /sys/bus/usb/devices/usb1/
}

check_auth_file_exists_and_exit_if_not()
{
    if [ ! -f "$auth_file" ]; then
        echo "Error: OxChief auth file ($auth_file) not found. Please login to OxChief to get the contents of this file."
        exit 1
    else
        echo "OxChief auth file ($auth_file) found."
    fi
}

# Function to build Docker device arguments based on USB devices
build_usb_docker_device_args()
{   
    usb_info_file="${1:-devices.txt}"
    usb_names_file="${2:-device-names.txt}"
    # Create $project_path/temp directory if it doesn't exist
    mkdir -p $project_path/temp

    # Set variable temp_files_path to the path of the temp directory
    temp_files_path="$project_path/temp"

    # If we change the name of the file devices.txt here, then we need to also change
    # it at Constants.DEVICES_FILENAME in src/constants.py

    echo "Gathering attached usb devices info"
    list_usb_info_path="$temp_files_path/$usb_info_file"
    list_usb_names_path="$temp_files_path/$usb_names_file"
    
    list_usb_info > "$list_usb_info_path"

    # Initialize a counter
    attempt=0

    # Loop up to 10 times
    while [ $attempt -lt 10 ]; do
        # Check if the file exists
        if [ -f "$list_usb_info_path" ]; then
            echo "$list_usb_info_path file successfully generated."
            break # Exit the loop if the file is found
        else
            echo "File does not exist, attempting to generate..."
            list_usb_info > "$list_usb_info_path" # Attempt to generate the file
        fi

        # Increment the attempt counter
        attempt=$((attempt + 1))

        # Sleep for a bit before trying again, optional
        sleep 1
    done

    # Check if the file still doesn't exist after 10 attempts
    if [ ! -f "$list_usb_info_path" ]; then
        echo "Failed to generate the file after 10 attempts, exiting."
        exit 1
    fi

    list_usb_names > "$list_usb_names_path"

    # Initialize a counter
    attempt=0

    # Loop up to 10 times
    while [ $attempt -lt 10 ]; do
        # Attempt to generate the file
        list_usb_names > "$list_usb_names_path"
        
        # Check if the file exists
        if [ -f "$list_usb_names_path" ]; then
            echo "$list_usb_names_path file successfully generated."
            break # Exit the loop if the file is found
        else
            echo "File does not exist, attempting to generate again..."
        fi

        # Increment the attempt counter
        attempt=$((attempt + 1))

        # Sleep for a bit before trying again, optional
        sleep 1
    done

    # Check if the file still doesn't exist after 10 attempts
    if [ ! -f "$list_usb_names_path" ]; then
        echo "Failed to generate the file after 10 attempts, exiting."
        exit 1
    fi

    DOCKER_DEVICE_ARGS=""

    while IFS= read -r line
    do
        DOCKER_DEVICE_ARGS+="--device=$line "
    done < "$list_usb_names_path"
}

exec_oxchief_pipe()
{
    # This script continuously evaluates the commands in the "oxpipe" fifo pipe file 
    # and exectes these commands on the host as shell commands -- it's the way we 
    # communicate privileged commands to the host raspberry pi from the oxchief 
    # python code running in the docker container. Specifically, we use this 
    # pipe to:
    #
    # 1. reboot the raspberry pi
    # 2. restart the oxchief docker container
    # 3. start/stop the tailscale service
    while true; do eval "$(cat $project_path/oxpipe)" &> $project_path/oxpipeoutput.txt; done
}

# Define a function to run the Docker container
run_docker_container() 
{
    DOCKER_RUN_STRING="docker run -itd --env-file $auth_file -v $project_path/config.ini:/usr/src/app/config.ini -v $project_path/temp:/usr/src/app/temp -v $project_path/oxpipe:/oxpipe --log-opt max-size=100m --log-opt max-file=5 $extra_stuff $DOCKER_DEVICE_ARGS -p 3339:3339 oxchief/oxchief-client:$DOCKER_OX_CLIENT_VERSION $container_mode"
    echo "$DOCKER_RUN_STRING"
    $DOCKER_RUN_STRING
}

# Define a function to run the RealSense Docker container
run_realsense_container() 
{
    DOCKER_RUN_STRING="docker run -itd --privileged -v $project_path/config.ini:/usr/src/app/config.ini -v $project_path/cfg:/usr/src/app/cfg -v $project_path/temp:/usr/src/app/temp --log-opt max-size=100m --log-opt max-file=5 $DOCKER_DEVICE_ARGS -p 3338:3338 oxchief/oxchief-realsense:$DOCKER_REALSENSE_VERSION"
    echo "$DOCKER_RUN_STRING"
    $DOCKER_RUN_STRING
}

autopilot()
{
    check_auth_file_exists_and_exit_if_not
    restore_usb_access
    container_mode="autopilot_client"
    delete_all_files_in_temp_folder
    echo "Running autopilot"
    build_usb_docker_device_args
    run_docker_container
    # BLUETOOTH TESTING NOTES
    # as of Jan 28, 2023, the autopilot raspberry pi was 64 bit and the base 
    # station raspberry pi was 32 bit -- I don't know if this is why we 
    # have to go slightly different directions to get bluetooth 
    # running on them -- at the moment I prefer this approach 
    # (i.e. just mapping the dbus volume) because it doesn't
    # require stopping the bluetooth service on the host 
    # via the service_bluetooth_stop.sh script 
    # which feels clunky
    #
    # extra_stuff="-v /var/run/dbus:/var/run/dbus"
}

base()
{
    check_auth_file_exists_and_exit_if_not
    restore_usb_access
    container_mode="base_station_client"
    delete_all_files_in_temp_folder
    echo "Running base station"
    build_usb_docker_device_args
    run_docker_container
}

obstacle_avoidance()
{
    restore_usb_access
    echo "Running obstacle avoidance"
    build_usb_docker_device_args "devices2.txt" "device-names2.txt"
    run_realsense_container
}

# Display usage information
usage() 
{
    echo "Usage: $0 [option]"
    echo "Options:"
    echo "  list_usb_names   List the names of all USB devices connected to the system"
    echo "  list_usb_info    List the names and serial numbers of all USB devices connected to the system"
    echo "  version          Show script version"
    echo "  autopilot        Run the autopilot logic"
    echo "  base             Run the base station logic"
    echo "  obstacles        Run the Intel Realsense obstacle detection logic"
    echo "  pipe             Run the oxchief pipe loop that executes commands from the container via the oxpipe file"
    echo "  help             Show this help message"
    # Add more options as needed...
}

# main function: Entry point of the script
# Parameters:
#   $1 (optional): Mode of operation. Available modes are:
#     - list_usb_names: Lists the names of connected USB devices
#     - list_usb_info: Lists detailed information about connected USB devices
#     - version: Displays the script version
#     - autopilot: Executes the autopilot logic
#     - base: Executes the base station logic
#     - obstacles: Executes the obstacle avoidance logic
#     - pipe: Executes the oxchief pipe loop
#     - help (default): Displays the usage information
main() 
{
    mode="${1,,}"
    if [ $# -eq 0 ]; then
        mode='help'
    elif [ $# -ne 1 ]; then
        echo "Too many parameters!"
        mode='help'
    fi

    # Parse command-line arguments
    case $mode in
        list_usb_names)
            list_usb_names
            ;;
        list_usb_info)
            list_usb_info
            ;;
        version)
            echo "Script version: $VERSION"
            ;;
        autopilot)
            autopilot
            ;;
        base)
            base
            ;;
        obstacles)
            obstacle_avoidance
            ;;
        pipe)
            exec_oxchief_pipe
            ;;
        help|*)
            usage
            ;;
    esac
}


# Check if the script is being run directly or sourced.
# If the script is being run directly, call the main
# function with the provided command-line arguments.
# If the script is being sourced, do nothing.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi