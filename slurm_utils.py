"""
Utility functions for managing Slurm nodes.
"""

import subprocess

def generate_node_config(cpus, memory, feature):
    """Generate a Slurm node configuration string dynamically."""
    return f"CPUs={cpus} RealMemory={memory} Feature={feature}"

def add_vm_to_slurm(vm_ip, settings):
    """Add the VM to the Slurm cluster dynamically using slurmd -Z."""
    try:
        print(f"Adding VM with IP {vm_ip} to Slurm cluster dynamically...")
        node_config = generate_node_config(
            cpus=settings["cpus"],
            memory=settings["memory"],
            feature=settings["feature"],
        )
        slurmd_command = f"slurmd -Z --conf '{node_config}'"
        subprocess.run(
            ["ssh", f"root@{vm_ip}", slurmd_command],
            check=True,
        )
        print(f"VM with IP {vm_ip} dynamically registered with Slurm.")
    except subprocess.CalledProcessError as e:
        print(f"Error dynamically registering VM with Slurm: {e}")
