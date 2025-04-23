"""
Main module for managing OpenStack VMs and Slurm integration.
"""

import time
import subprocess
from openstack import connection
from config import parse_config_and_args
from openstack_utils import create_vm, get_running_vms, get_next_vm_name
from slurm_utils import add_vm_to_slurm

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

def handle_vm_creation(conn, settings, vm_name):
    """Create a VM and configure it using a local Ansible playbook."""
    server = create_vm(conn, vm_name, None, settings)  # No cloud-init file
    vm_ip = None
    network_name = settings["vm_network"]
    if network_name in server.addresses:
        for address in server.addresses[network_name]:
            if address.get("OS-EXT-IPS:type") == "fixed":
                vm_ip = address.get("addr")
                break
    if not vm_ip:
        raise RuntimeError(f"Failed to retrieve IP address for VM {vm_name} on network {network_name}.")

    # Run the local playbook
    try:
        print(f"Configuring VM {vm_name} with IP {vm_ip} using Ansible playbook...")
        subprocess.run(
            [
                "ansible-playbook",
                settings["playbook_path"],
                "-i", f"{vm_ip},",
                "--private-key", settings["key_name"],
                "-u", settings["ansible_user"]
            ],
            check=True,
        )
        print(f"VM {vm_name} configured successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error configuring VM {vm_name} with Ansible: {e}")
        raise

    add_vm_to_slurm(vm_ip, settings)

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
    # Ensure at least one VM is running on start
    running_vms = len(get_running_vms(conn))
    if running_vms < 1:
        print("No VMs are running. Starting one VM to meet the minimum requirement.")
        vm_name = get_next_vm_name(conn, settings["vm_name_prefix"], settings["max_vms"])
        if vm_name:
            handle_vm_creation(conn, settings, vm_name)
        else:
            print("No available VM names. Maximum VM limit reached.")
    while True:
        running_vms = get_running_vms(conn)
        print(f"Currently running VMs: {len(running_vms)}")
        pending_jobs = get_slurm_queue()
        print(f"Pending jobs: {pending_jobs}")

        if pending_jobs == 0 and len(running_vms) > settings["min_vms"]:
            print("No jobs in the queue. Deleting excess VMs.")
            for vm_name in running_vms[settings["min_vms"]:]:
                delete_vm(conn, vm_name)

        elif len(running_vms) < settings["min_vms"]:
            print(f"Starting VMs to meet minimum requirement of {settings['min_vms']} VMs.")
            for _ in range(settings["min_vms"] - len(running_vms)):
                vm_name = get_next_vm_name(conn, settings["vm_name_prefix"], settings["max_vms"])
                if not vm_name:
                    print("No available VM names. Maximum VM limit reached.")
                    break
                handle_vm_creation(conn, settings, vm_name)

        elif len(running_vms) < settings["max_vms"] and pending_jobs >= settings["min_pending_jobs"]:
            vm_name = get_next_vm_name(conn, settings["vm_name_prefix"], settings["max_vms"])
            if not vm_name:
                print("No available VM names. Maximum VM limit reached.")
                break
            handle_vm_creation(conn, settings, vm_name)

        else:
            print(f"Maximum VM limit of {settings['max_vms']} reached. No new VMs will be created.")

        time.sleep(settings["check_interval"])

if __name__ == "__main__":
    main()
