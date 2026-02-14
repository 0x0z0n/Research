import os
import tarfile
import shutil
from http.server import SimpleHTTPRequestHandler
import socketserver
import socket

# --- CONFIGURATION ---
PORT = 8080
EXPORT_DIR = "/tmp/log_export"
ARCHIVE_NAME = "browsed_logs.tar.gz"
LOGS_TO_HUNT = [
    "/var/log/auth.log",
    "/var/log/syslog",
    "/var/log/nginx/access.log",
    "/var/log/nginx/error.log",
    "/var/log/apache2/access.log",
    "/var/log/apache2/error.log",
    "/opt/extensiontool/logs/"  # App specific logs if they exist
]

def main():
    # 1. Prepare Staging Directory
    if os.path.exists(EXPORT_DIR):
        shutil.rmtree(EXPORT_DIR)
    os.makedirs(EXPORT_DIR)
    
    print(f"[+] Staging directory created at {EXPORT_DIR}")

    # 2. Copy Logs
    # We iterate through the list and copy what exists
    copied_count = 0
    for log_path in LOGS_TO_HUNT:
        if os.path.exists(log_path):
            try:
                # If it's a directory, copy the whole tree
                if os.path.isdir(log_path):
                    shutil.copytree(log_path, os.path.join(EXPORT_DIR, os.path.basename(log_path)))
                # If it's a file, copy the file
                else:
                    shutil.copy2(log_path, EXPORT_DIR)
                print(f"    - Found and copied: {log_path}")
                copied_count += 1
            except PermissionError:
                print(f"    [!] Permission Denied (Run as Root!): {log_path}")
        else:
            pass # File not found, skip silently

    if copied_count == 0:
        print("[!] No logs found! Are you running as root?")
        return

    # 3. Create Archive (TarGZ)
    archive_path = os.path.join(EXPORT_DIR, ARCHIVE_NAME)
    print(f"[+] Compressing logs into {ARCHIVE_NAME}...")
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(EXPORT_DIR, arcname=os.path.basename(EXPORT_DIR))

    # 4. Move Archive to Current Directory for serving
    final_serve_path = os.path.join(os.getcwd(), ARCHIVE_NAME)
    shutil.move(archive_path, final_serve_path)
    
    # Clean up staging
    shutil.rmtree(EXPORT_DIR)

    # 5. Start HTTP Server
    # Get IP for display purposes
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()

    print(f"\n[+] HOSTING LOGS NOW.")
    print(f"[+] Download Link: http://{IP}:{PORT}/{ARCHIVE_NAME}")
    print(f"[+] Press Ctrl+C to stop the server after downloading.\n")

    # Start the server
    handler = SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[+] Server stopped. Cleaning up...")
            if os.path.exists(final_serve_path):
                os.remove(final_serve_path)
            print("[+] Cleanup complete.")

if __name__ == "__main__":
    main()
