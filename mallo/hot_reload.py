"""
Hot reload functionality for Mallo Framework
"""
import os
import sys
import time
import signal
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ReloadHandler(FileSystemEventHandler):
    """
    Handles file system events and triggers reload
    """
    def __init__(self, callback, watch_paths=None):
        self.callback = callback
        self.last_trigger = 0
        self.cooldown = 1.0 # Cooldown period in seconds
        self.watch_extensions = {
            '.py', '.html', '.htm', '.css', '.js', '.json', '.txt'
        }
        self.ignore_parts = {
            '__pycache__', '.pytest_cache', '.git', '.venv', '.idea'
        }
        self.file_signatures = {}
        self._prime_signatures(watch_paths or ['.'])

    def _signature(self, path):
        try:
            stat = os.stat(path)
            return (stat.st_mtime_ns, stat.st_size)
        except OSError:
            return None

    def _prime_signatures(self, watch_paths):
        for root in watch_paths:
            if not os.path.exists(root):
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                normalized_dir = dirpath.replace('\\', '/')
                if any(part in normalized_dir for part in self.ignore_parts):
                    continue

                for filename in filenames:
                    path = os.path.join(dirpath, filename)
                    if not self._should_reload(path):
                        continue
                    sig = self._signature(path)
                    if sig is not None:
                        self.file_signatures[path] = sig

    def _should_reload(self, src_path):
        normalized = src_path.replace('\\', '/')

        # Ignore noisy/system paths.
        if any(part in normalized for part in self.ignore_parts):
            return False

        filename = normalized.rsplit('/', 1)[-1]

        # Ignore common temporary editor files.
        if (
            filename.startswith('.')
            or filename.endswith('~')
            or filename.endswith('.tmp')
            or filename.endswith('.swp')
            or filename.endswith('.swx')
            or filename.endswith('.bak')
        ):
            return False

        _, ext = os.path.splitext(filename.lower())
        return ext in self.watch_extensions

    def _process_event_path(self, src_path):
        if not self._should_reload(src_path):
            return

        current_signature = self._signature(src_path)
        previous_signature = self.file_signatures.get(src_path)

        if current_signature is None:
            return

        if previous_signature is None:
            # New file: track and trigger reload once.
            self.file_signatures[src_path] = current_signature
        elif previous_signature == current_signature:
            # Duplicate/no-op event.
            return
        else:
            self.file_signatures[src_path] = current_signature

        current_time = time.time()
        if current_time - self.last_trigger > self.cooldown:
            self.last_trigger = current_time
            print(f"\n * Detected change in: {src_path}")
            self.callback()

    def on_modified(self, event):
        # Ignore directory modifications
        if event.is_directory:
            return
        self._process_event_path(event.src_path)

    # Some editors save via "create new file + move/replace".
    def on_created(self, event):
        if event.is_directory:
            return
        self._process_event_path(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        self._process_event_path(event.dest_path)

class HotReloader:
    """
    Manages hot reload functionality
    """
    def __init__(self, app):
        self.app = app
        self.process = None
        self.observer = None
        self.watch_paths = ['.'] # Directory to watch

    def run(self, host, port):
        """
        Start the server with hot reload
        :param host:
        :param port:
        :return:
        """
        print("* Hot reload is enable")
        print("* Watching for file changes...")

        #Start server in a subprocess
        self.start_server_process(host, port)

        # Start file watcher
        self.start_watcher()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def start_server_process(self, host, port):
        """
        Start the server as a subprocess

        :param host:
        :param port:
        :return:
        """
        env = os.environ.copy()
        env['MALLO_HOT_RELOAD'] = '1'

        # Get the main script path
        main_script = sys.argv[0]

        self.process = subprocess.Popen(
            [sys.executable, main_script],
            env=env
        )

    def start_watcher(self):
        """
        Start watching for file changes
        :return:
        """
        self.observer = Observer()
        handler = ReloadHandler(self.reload_server, self.watch_paths)

        # Watch python files in current directory and subdirectories
        for path in self.watch_paths:
            if os.path.exists(path):
                self.observer.schedule(handler, path, recursive=True)

        self.observer.start()

    def reload_server(self):
        """
        Reload the server process

        :return:
        """
        print(" * Reloading server....")

        # kill the old process
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

        # get the main script path and arguments
        main_script = sys.argv[0]

        # start new process
        env = os.environ.copy()
        env['MALLO_HOT_RELOAD'] = '1'

        self.process = subprocess.Popen(
            [sys.executable, main_script] + sys.argv[1:],
            env=env
        )

        print("* Reload complete!")

    def stop(self):
        """
        Stop the hot reloader and server

        :return:
        """
        print("\n * Stopping server....")
        if self.observer:
            self.observer.stop()
            self.observer.join()

        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

        print("* Server stopped")
