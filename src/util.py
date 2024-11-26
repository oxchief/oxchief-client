"""
Author: Wayne Baswell

Potentially reusable functionality that doesn't fit into another *_util module. 
"""
import asyncio

from asyncio import Task
from typing import Callable

running_tasks = set()

def asyncio_create_task_disappear_workaround(
    some_async_func:Callable[..., asyncio.Future]) -> Task:
    """
    Workaround for asyncio.create_task garbage collection behavior where we keep 
    a reference to the task until it's done to prevent unintend garbage 
    collection (and thus potentially premature termination)

    Parameters:
        some_async_func (Callable[..., asyncio.Future]): Async function that
            we want to call without it disappearing prematurely
            due to garbage collection behavior

    Returns:
        a Task object

    See Also:
        - https://stackoverflow.com/questions/71938799/python-asyncio-create-task-really-need-to-keep-a-reference
        - https://github.com/python/cpython/issues/88831
    """
    task = asyncio.create_task(some_async_func)
    running_tasks.add(task)
    task.add_done_callback(lambda t: running_tasks.remove(t))
    return task

def heading_difference(heading1:float, heading2:float) -> float:
    """
    Find delta (in degrees) between two headings

    Args:
        heading1 (float): first heading
        heading2 (float): second heading

    Returns:
        float: delta between two headings
    """
    # Ensure headings are within the range [0, 360] degrees
    heading1 = heading1 % 360
    heading2 = heading2 % 360

    # Calculate the angular difference between the headings
    angle_difference = abs(heading1 - heading2)

    # Take the smaller of the two possible differences
    if angle_difference > 180:
        angle_difference = 360 - angle_difference

    return angle_difference

def max_heading_difference(headings: list[float]) -> float:
    """
    Maximum heading difference between any two numbers in a list of headings

    Args:
        headings (list[float]): List of headings

    Returns:
        float: Maximum difference in degrees
    """
    max_diff = 0
    num_headings = len(headings)

    # Iterate through all combinations of elements in the list
    for i in range(num_headings):
        for j in range(i + 1, num_headings):
            diff = heading_difference(headings[i], headings[j])
            max_diff = max(max_diff, diff)

    return max_diff
