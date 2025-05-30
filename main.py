"""
Main module for managing OpenStack VMs and Slurm integration.
"""

import time
import subprocess
import socket  # Add this import for checking SSH connectivity
from openstack import connection
from config import parse_config_and_args
from openstack_utils import create_vm, get_running_vms, get_next_vm_name

def get_slurm_queue():
    """Retrieve the number of pending jobs from the Slurm queue."""
    try:
        result = subprocess.run(
            ["squeue", "--states=PD", "--noheader"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving Slurm queue: {e.stderr}")
        return 0

def wait_for_ssh(vm_ip, timeout=300, interval=5):
    """Wait for the SSH port to become available."""
    print(f"Waiting for SSH on {vm_ip}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((vm_ip, 22), timeout=10):
                print(f"SSH is available on {vm_ip}.")
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(interval)
    raise RuntimeError(f"SSH not available on {vm_ip} after {timeout} seconds.")

def handle_vm_creation(conn, settings, vm_name):
    """Create a VM and configure it using a local Ansible playbook."""
    server = create_vm(conn, vm_name, settings)
    vm_ip = None
    network_name = settings["vm_network"]
    if network_name in server.addresses:
        for address in server.addresses[network_name]:
            if address.get("OS-EXT-IPS:type") == "fixed":
                vm_ip = address.get("addr")
                break
    if not vm_ip:
        raise RuntimeError(f"Failed to retrieve IP address for VM {vm_name} on network {network_name}.")

    # Wait for SSH to become available
    wait_for_ssh(vm_ip)

    # Run the local playbook
    try:
        print(f"Configuring VM {vm_name} with IP {vm_ip} using Ansible playbook...")
        subprocess.run(
            [
                "ansible-playbook",
                settings["playbook_path"],
                "-i", f"{vm_ip},",
                "--private-key", settings["private_key_file"],
                "-u", settings["ansible_user"],
                "--ssh-common-args='-o StrictHostKeyChecking=no'",
            ],
            check=True,
        )
        print(f"VM {vm_name} configured successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error configuring VM {vm_name} with Ansible: {e}")
        raise

def delete_vm(conn, vm_name):
    """Delete a VM by name."""
    try:
        print(f"Deleting VM: {vm_name}")
        server = conn.compute.find_server(vm_name)
        if server:
            conn.compute.delete_server(server.id)
            print(f"VM {vm_name} deleted successfully.")
        else:
            print(f"VM {vm_name} not found.")
    except Exception as e:
        print(f"Error deleting VM {vm_name}: {e}")

def main():
    settings = parse_config_and_args()
    conn = connection.Connection(
        auth_url=settings["auth_url"],
        project_name=settings["project_name"],
        username=settings["username"],
        password=settings["password"],
        user_domain_name=settings["user_domain_name"],
        project_domain_name=settings["project_domain_name"],
    )
    idle_start_time = None  # Track when the queue became idle

    # Ensure at least one VM is running on start
    running_vms = get_running_vms(conn, settings["vm_name_prefix"])
    if len(running_vms) < 1:
        print("No VMs are running. Starting one VM to meet the minimum requirement.")
        vm_name = get_next_vm_name(conn, settings["vm_name_prefix"], settings["max_vms"])
        if vm_name:
            handle_vm_creation(conn, settings, vm_name)
        else:
            print("No available VM names. Maximum VM limit reached.")

    while True:
        running_vms = get_running_vms(conn, settings["vm_name_prefix"])
        print(f"Currently running VMs: {len(running_vms)} (Filtered by prefix: {settings['vm_name_prefix']})")
        print(f"Running VMs: {running_vms}")  # Debugging output to verify VM names
        pending_jobs = get_slurm_queue()
        print(f"Pending jobs: {pending_jobs}")

        if pending_jobs == 0:
            if idle_start_time is None:
                idle_start_time = time.time()  # Start tracking idle time
            idle_duration = (time.time() - idle_start_time) / 60  # Convert to minutes

            if len(running_vms) > settings["min_vms"]:
                print("No jobs in the queue. Deleting excess VMs.")
                vms_to_delete = [
                    vm_name for vm_name in running_vms[settings["min_vms"]:]
                    if vm_name.startswith(settings["vm_name_prefix"])
                ]
                if idle_duration >= settings["idle_time_before_deletion"]:
                    # Delete up to max_vms_to_delete VMs
                    for vm_name in vms_to_delete[:settings["max_vms_to_delete"]]:
                        delete_vm(conn, vm_name)
                else:
                    # Delete only one VM at a time
                    if vms_to_delete:
                        delete_vm(conn, vms_to_delete[0])
        else:
            idle_start_time = None  # Reset idle time if there are pending jobs

        if len(running_vms) < settings["min_vms"]:
            print(f"Starting VMs to meet minimum requirement of {settings['min_vms']} VMs.")
            for _ in range(settings["min_vms"] - len(running_vms)):
                vm_name = get_next_vm_name(conn, settings["vm_name_prefix"], settings["max_vms"])
                if not vm_name:
                    print("No available VM names. Maximum VM limit reached.")
                    break
                handle_vm_creation(conn, settings, vm_name)

        elif len(running_vms) < settings["max_vms"] and pending_jobs >= settings["min_pending_jobs"]:
            print(f"Creating a new VM. Current running VMs: {len(running_vms)}, Max VMs: {settings['max_vms']}")
            vm_name = get_next_vm_name(conn, settings["vm_name_prefix"], settings["max_vms"])
            if not vm_name:
                print("No available VM names. Maximum VM limit reached.")
                break
            handle_vm_creation(conn, settings, vm_name)

        else:
            print(f"Current running VMs: {len(running_vms)}, Max VMs: {settings['max_vms']}")

        time.sleep(settings["check_interval"])

if __name__ == "__main__":
    main()
