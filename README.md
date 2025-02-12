# watcheagle: A Simple File Watcher and Process Restarter (Fork of watchcat)

`watcheagle` is a lightweight command-line tool that monitors a directory for file changes and automatically restarts a specified process when a modification is detected. It's designed for development environments where you want to automatically reload your application on code changes. This project is based on the original `watchcat` but has been simplified and optimized for ease of use.

## Goal

The primary goal of `watcheagle` is to provide a simple, reliable, and efficient way to automatically restart a process when files in a directory change. This is useful for rapid development cycles, automatically testing code, or automatically refreshing content on file updates.

## Key Features

-   **Easy to Use:** Simple command-line interface.
-   **Automatic Process Restart:** Restarts your application whenever relevant files are modified.
-   **Fork of watchcat:** Leaner and more straightforward, building upon the foundation of watchcat.
-   **Optional Source Directory:** Specify the directory to watch, defaulting to the current directory.

## Installation

```bash
pip install watcheagle
```

## Usage

Invoke `watcheagle` from the command line, providing the command to execute and optionally the directory to watch.

```
python -m watcheagle <command_to_execute> [--source <directory>]
```

### Examples

1.  **Restarting a Python script in the current directory:**

    ```bash
    python -m watcheagle python main.py
    ```

    This command will execute `python main.py` and watch for changes in the current directory. Any file modification will trigger a restart of the `main.py` script.

2.  **Restarting a Node.js application monitoring a specific directory:**

    ```bash
    python -m watcheagle node app.js --source ./src
    ```

    This command will execute `node app.js` and monitor the `./src` directory.

3.  **Using with a shell script:**

    ```bash
    python -m watcheagle ./build_and_run.sh --source ./code
    ```

    This command assumes you have a `build_and_run.sh` script that builds your project and then runs it. It will watch the `./code` directory for changes.

4.  **Monitoring current directory with react application**

    ```bash
    python -m watcheagle yarn start --source ./
    ```

    This is equivalent to running `yarn start`, and the tool will restart yarn if a file is changed in the current directory

### Optional Arguments

-   `--source <directory>`: Specify the directory to watch for changes. If not provided, `watcheagle` defaults to the current working directory.

## .watchignore (Excluding Files and Directories - Original watchcat feature)

To exclude specific files or directories from being monitored, create a `.watchignore` file in the root directory being watched. Use `fnmatch` patterns. The changes may occur as implemented in watchcat original(exclude implementation).

### Example .watchignore Usage

```
# Ignore the logs directory and its output
logs/
*.log

# Ignore temp files
temp_*

```

## Contributing

Contributions are welcome! Feel free to fork the repository, make improvements, and submit pull requests.

## License

This project is under the MIT License.
