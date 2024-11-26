#!/bin/bash

trap exit SIGINT  # Ensure immediate exit on Ctrl-C

docker_logs_follow() {
  # Get a list of running container IDs
  local cids=$(docker ps -q)

  # Check if there are any containers
  if [[ -z "$cids" ]]; then
    echo "No running Docker containers found."
    return
  fi

  # Follow logs with trap in subshells
  for cid in $cids; do
    (trap exit SIGINT; docker logs -f "$cid" --tail 100) &  # Trap Ctrl-C in subshell
  done

  # Wait for background processes to finish
  wait
}

docker_logs_follow

echo "Following logs of all active Docker containers. Press Ctrl-C to exit."

