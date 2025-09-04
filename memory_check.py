import subprocess
import time
import psutil
import os


def main():
    """
    Starts the FastAPI server as a separate process and measures its memory usage
    after the models have loaded. It correctly measures the parent process and all
    child worker processes.
    """
    print("--- Starting FastAPI Server for Memory Check ---")

    # Command to start your Uvicorn server
    # This assumes your main application instance is named 'app' in 'main.py'
    command = ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]

    # Start the server as a background process
    try:
        server_process = subprocess.Popen(command)
        print(f"Server process started with PID: {server_process.pid}")

        # Give the server time to start up and load all the models
        print("Waiting 15 seconds for models to load...")
        time.sleep(15)

        # Find the process and measure its memory
        try:
            parent_process = psutil.Process(server_process.pid)

            # Get all child processes spawned by the server
            children = parent_process.children(recursive=True)
            all_processes = [parent_process] + children

            total_memory_bytes = 0
            for proc in all_processes:
                total_memory_bytes += proc.memory_info().rss

            # Get memory usage in bytes and convert to megabytes
            memory_mb = total_memory_bytes / (1024 * 1024)

            print("\n--- Memory Usage Report ---")
            print(f"Found {len(all_processes)} process(es) (1 parent, {len(children)} child/worker).")
            print(f"✅ Backend is using approximately: {memory_mb:.2f} MB")
            print("---------------------------\n")

        except psutil.NoSuchProcess:
            print(f"❌ Could not find process with PID {server_process.pid}. The server may have failed to start.")
            print("Check the server logs for errors.")

    finally:
        # Ensure the server process is terminated when the script is done
        if 'server_process' in locals() and server_process.poll() is None:
            print("--- Shutting down the server ---")
            server_process.terminate()
            server_process.wait()
            print("Server has been stopped.")


if __name__ == "__main__":
    main()

