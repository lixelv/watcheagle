import subprocess  # Used for executing shell commands and managing processes.
import argparse  # Used for parsing command-line arguments.
import asyncio  # Used for asynchronous programming.
import shlex  # Used for splitting strings into shell-like syntax.
import time  # Used for time-related operations (e.g., throttling).
import os  # Used for interacting with the operating system (e.g., file paths).
import sys  # Used for accessing system-specific parameters and functions.
import logging  # Used for logging messages.
import platform  # Used for determining the operating system.
import fnmatch  # Used for filename matching with shell-style patterns.

from collections import (
    defaultdict,
)  # Used for creating dictionaries with default values.

from watchdog.events import (
    FileSystemEventHandler,
)  # Used for handling file system events.
from watchdog.observers import Observer  # Used for observing file system changes.

# ANSI escape codes for colors (used for colored terminal output)
GRAY = "\x1b[38;20m"
GREEN = "\x1b[32;1m"
YELLOW = "\x1b[33;1m"
RED = "\x1b[31;1m"
BOLD_RED = "\x1b[31;1m"
RESET = "\x1b[0m"


# Custom formatter with color (uses ANSI escape codes to colorize log messages)
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        log_message = super().format(record)
        if record.levelno == logging.INFO:
            return f"{GRAY}{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}{RESET} {GREEN}[info]{RESET} {log_message}"
        elif record.levelno == logging.WARNING:
            return f"{GRAY}{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}{RESET} {YELLOW}[warning]{RESET} {log_message}"
        elif record.levelno >= logging.ERROR:
            return f"{GRAY}{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}{RESET} {RED}[error]{RESET} {log_message}"
        else:
            return f"{GRAY}{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}{RESET} [unknown] {log_message}"


# Configure logging (sets up logging level and handler)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()  # Outputs log messages to the console
formatter = ColoredFormatter("%(message)s")  # Sets the custom colorized formatter
handler.setFormatter(formatter)  # Assigns the formatter to the handler
logger.addHandler(handler)  # Adds the handler to the logger


def load_ignore_patterns(watch_directory):
    """
    Loads ignore patterns from a .watchignore file, allowing comma-separated entries.

    Args:
        watch_directory (str): The directory being watched for changes.

    Returns:
        list: A list of ignore patterns loaded from the .watchignore file.
              Returns an empty list if the file does not exist.
    """
    ignore_patterns = []
    ignore_file_path = os.path.join(watch_directory, ".watchignore")
    if os.path.exists(ignore_file_path):
        try:
            with open(ignore_file_path, "r") as f:
                for line in f:
                    line = line.strip()  # Remove leading/trailing whitespace
                    if line and not line.startswith("#"):  # Ignore comments
                        # Split by comma and strip each part
                        patterns = [p.strip() for p in line.split(",")]
                        ignore_patterns.extend(patterns)
            logging.info(
                f"Loaded ignore patterns from {ignore_file_path}: {ignore_patterns}"
            )
        except Exception as e:
            logging.error(f"Error reading .watchignore: {e}")
    else:
        logging.info("No .watchignore file found.")
    return ignore_patterns


def is_ignored(path, ignore_patterns, watch_directory):
    """
    Checks if the given path should be ignored based on the patterns in .watchignore.

    Args:
        path (str): The full path to the file or directory being checked.
        ignore_patterns (list): A list of ignore patterns.
        watch_directory (str): The directory being watched.

    Returns:
        bool: True if the path should be ignored, False otherwise.
    """
    relative_path = os.path.relpath(path, watch_directory)  # get directory

    for pattern in ignore_patterns:
        # Check if the relative path matches the ignore pattern, if not, try just file name
        if fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch(
            os.path.basename(path), pattern
        ):
            logging.debug(f"Path '{relative_path}' matches ignore pattern '{pattern}'")
            return True

        # Check if the final path is a slash
        if os.path.isdir(path) and relative_path.endswith("/"):
            logging.debug("Removing final slash from relative path")
            relative_path = relative_path[:-1]

        if os.path.isdir(path) and relative_path.endswith("\\"):
            logging.debug("Removing final backslash from relative path")
            relative_path = relative_path[:-1]

    # Ensure directory matching
    for pattern in ignore_patterns:
        if os.path.isdir(path):
            if fnmatch.fnmatch(relative_path + "/", pattern) or fnmatch.fnmatch(
                os.path.basename(path) + "/", pattern
            ):
                logging.debug(
                    f"Path '{relative_path}' matches ignore DIRECTORY pattern '{pattern}'"
                )
                return True

    return False


class Throttle:
    """
    A decorator that throttles the execution of a function to a certain rate.
    """

    def __init__(self, delay=0.05):
        """
        Initialize the Throttler with a delay in seconds.

        Args:
            delay (float): The minimum time (in seconds) between function calls.
        """
        self.delay = delay  # Minimum time between calls
        self.last_called = defaultdict(
            lambda: 0
        )  # Time of the last call for different keys

    def __call__(self, func):
        """
        Decorator that returns a wrapper function to throttle the execution of the input function.

        Args:
            func (callable): The function to be throttled.

        Returns:
            callable: A wrapper function that throttles the execution of the input function.
        """

        async def wrapper(*args, **kwargs):
            key = args[0].src_path  # Extract key from arguments, type: ignore
            now = time.time()
            if now - self.last_called[key] > self.delay:
                self.last_called[key] = now
                return await func(*args, **kwargs)

        return wrapper


async def observe(path, EventHandler, ignore_patterns):
    """
    Sets up the watchdog observer to monitor a directory for file system events.

    Args:
        path (str): The path to the directory to observe.
        EventHandler (class): The event handler class to use (must inherit from FileSystemEventHandler).
        ignore_patterns (list): A list of ignore patterns to exclude from monitoring.
    """
    event_handler = EventHandler(
        ignore_patterns, path
    )  # Create new event handler, passing ignore patterns # type: ignore
    observer = Observer()
    try:
        observer.schedule(
            event_handler, path, recursive=True
        )  # Schedule the event handler to watch the directory recursively
        observer.start()  # Start the observer thread

        try:
            while True:
                await asyncio.sleep(30)  # Keep the observer running
        except asyncio.CancelledError:  # Handle asyncio cancellation
            logging.info("Observer cancelled.")
        finally:
            observer.stop()  # Stop the observer before exiting
            observer.join()  # Wait for the observer thread to finish
    except OSError as e:  # Handle OS errors
        logging.error(f"OSError in observe: {e}")
    except Exception as e:  # Handle other exceptions
        logging.exception(f"Unexpected error in observe: {e}")


def watch_decorator(path, ignore_patterns, *args, **kwargs):
    """
    A decorator that sets up file system watching using the watchdog library.

    Args:
        path (str): The path to the directory to be watched recursively.
        ignore_patterns (list):  A list of ignore patterns to exclude from monitoring.

    Returns:
        callable: A decorator that can be applied to a function.
    """
    loop = asyncio.get_event_loop()

    def decorator(func):
        @Throttle()
        async def throttled(event, *args, **kwargs):
            # type: ignore
            func(event, *args, **kwargs)

        class IgnoredEventHandler(FileSystemEventHandler):  # type: ignore # EventHandler
            def __init__(self, ignore_patterns, watch_directory):
                super().__init__()
                self.ignore_patterns = ignore_patterns
                self.watch_directory = watch_directory

            def on_any_event(self, event):
                """
                Handles any file system event, filtering ignored events.

                Args:
                    event (FileSystemEvent):  The file system event being handled.
                """
                if is_ignored(
                    event.src_path, self.ignore_patterns, self.watch_directory
                ):
                    logging.debug(f"Ignoring event for: {event.src_path}")
                    return

                try:
                    asyncio.run_coroutine_threadsafe(
                        throttled(event, *args, **kwargs), loop
                    )  # type: ignore
                except Exception as e:
                    logging.exception(f"Error in IgnoredEventHandler: {e}")

        # Start watching for file system events using the IgnoredEventHandler  # type: ignore
        asyncio.create_task(observe(path, IgnoredEventHandler, ignore_patterns))
        return func

    return decorator


if platform.system() == "Windows":
    import psutil

    def kill_process_tree(pid, include_parent=True):
        """
        Kills a process and all its descendants on Windows.

        Args:
            pid (int): The process ID of the parent process.
            include_parent (bool): Whether to include the parent process in the kill list.
        """
        try:
            parent = psutil.Process(pid)
        except psutil.NoSuchProcess:
            logging.warning(f"Process with PID {pid} not found.")
            return
        children = parent.children(recursive=True)
        if include_parent:
            children.append(parent)
        for process in children:
            try:
                logging.info(
                    f"Terminating process with PID {process.pid} and name {process.name()}"
                )
                process.terminate()
            except psutil.NoSuchProcess:
                logging.warning(f"Process with PID {process.pid} not found.")
            except Exception as e:
                logging.error(f"Error terminating process {process.pid}: {e}")
        psutil.wait_procs(children, timeout=5)  # try to wait to terminate
        for process in children:  # try to gracefully remove all possible
            if process.is_running():
                try:
                    process.kill()
                    logging.warning(f"Process with PID {process.pid} was KILLED")
                except psutil.NoSuchProcess:
                    logging.warning(f"Process with PID {process.pid} not found.")
                except Exception as e:
                    logging.error(f"Error killing process {process.pid}: {e}")


else:  # Linux and macOS

    def kill_process_tree(pid, include_parent=True):
        """
        Kills a process and all its descendants on Linux/macOS.

        Args:
            pid (int): The process ID of the parent process.
            include_parent (bool): Whether to include the parent process in the kill list.
        """
        import os

        try:

            def kill(pid):
                logging.info(f"Terminating process with PID {pid}")
                os.kill(pid, 15)  # SIGTERM

            parent_pid = pid
            if include_parent:
                kill(parent_pid)
            else:
                logging.info(
                    f"Terminating process tree for PID {pid}, excluding the parent process itself."
                )

        except Exception as e:
            logging.error(f"Error terminating process tree for PID {pid}: {e}")


async def watcher(source: str, execution_command: str) -> None:
    """
    Watches a directory for file changes and executes a command when a change occurs.

    Args:
        source (str): The directory to watch. Defaults to the current working directory.
        execution_command (str): The command to execute when a file change occurs.
    """
    source = source or os.getcwd()  # set source to current directory, if source is none
    logging.info(f"Watching source directory: {source}")

    ignore_patterns = load_ignore_patterns(source)  # Load ignore patterns

    if execution_command is None:
        raise ValueError("Please specify source and execution command")

    command_list = shlex.split(
        execution_command
    )  # Split the command into a list of arguments
    process = None

    def kill_wrapper():
        """
        Kills the current running process including its children.
        """
        nonlocal process
        if process and process.pid:
            try:
                kill_process_tree(process.pid)
            except Exception as e:
                logging.error(f"Error during full process termination: {e}")

    @watch_decorator(
        source, ignore_patterns
    )  # Apply the watch decorator to the on_file_change function
    def on_file_change(event):
        """Event handler that is triggered when a watched file changes, restart current process."""
        nonlocal process
        logging.info(f"File changed: {event.src_path}")
        kill_wrapper()  # Kill the currently running process
        try:
            process = subprocess.Popen(
                command_list, shell=True
            )  # Start a new process, shell = True ensures execution also in pythons
            logging.info(f"New process started with PID: {process.pid}")
        except Exception as e:
            logging.exception(f"Error starting new process: {e}")

    try:
        process = subprocess.Popen(
            command_list, shell=True
        )  # Initial run to execute command in python
        logging.info(f"Starting process with PID: {process.pid}")
        while True:
            await asyncio.sleep(30)  # keep alive for sometime
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received. Shutting down...")
        kill_wrapper()  # Kill all process
    except asyncio.CancelledError:
        logging.info("Watcher cancelled.")
    finally:
        logging.info("Watcher exiting.")  # Log exit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Restart a process on file changes.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "exec_command",
        nargs="+",
        help="Command to execute.  All arguments after the script name are considered part of the command.\n"
        "Example: python watcheagle python main.py [--source <directory>]",
    )
    parser.add_argument(
        "--source",
        help="Directory to watch. Defaults to the current working directory.",
        default=os.getcwd(),
    )

    args = parser.parse_args()
    exec_command = " ".join(args.exec_command)  # Join the exec command arguments

    try:
        asyncio.run(watcher(args.source, exec_command))
    except KeyboardInterrupt:
        logging.info("Script interrupted by keyboard. Exiting...")
        sys.exit(0)
