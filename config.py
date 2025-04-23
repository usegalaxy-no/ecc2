"""
Configuration parser for OpenStack VM Service.
Handles merging of configuration file and command-line arguments.
"""

import argparse
import configparser

def parse_config_and_args():
    """Parse configuration file and command-line arguments."""
    parser = argparse.ArgumentParser(description="OpenStack VM Service")
    parser.add_argument("--config", type=str, default="config.ini", help="Path to config file")
    parser.add_argument("--auth_url", type=str, help="OpenStack auth URL")
    parser.add_argument("--project_name", type=str, help="OpenStack project name")
    parser.add_argument("--username", type=str, help="OpenStack username")
    parser.add_argument("--password", type=str, help="OpenStack password")
    parser.add_argument("--user_domain_name", type=str, help="OpenStack user domain name")
    parser.add_argument("--project_domain_name", type=str, help="OpenStack project domain name")
    parser.add_argument("--vm_flavor", type=str, help="VM flavor")
    parser.add_argument("--vm_image", type=str, help="VM image")
    parser.add_argument("--vm_network", type=str, help="VM network")
    parser.add_argument("--check_interval", type=int, help="Check interval in seconds")
    parser.add_argument("--min_vms", type=int, help="Minimum number of VMs")
    parser.add_argument("--max_vms", type=int, help="Maximum number of VMs")
    parser.add_argument("--memory", type=int, help="Memory for Slurm node (in MB)")
    parser.add_argument("--feature", type=str, help="Feature for Slurm node")
    parser.add_argument("--node_config", type=str, help="Custom Slurm node configuration string")
    parser.add_argument("--cpus", type=int, help="Number of CPUs for Slurm node")
    parser.add_argument("--vm_name_prefix", type=str, help="Prefix for VM names")
    parser.add_argument("--min_pending_jobs", type=int, help="Minimum pending jobs before creating a new VM")
    parser.add_argument("--key_name", type=str, help="Key pair name for the VM")
    parser.add_argument("--playbook_path", type=str, help="Path to the Ansible playbook")
    parser.add_argument("--ansible_user", type=str, help="Ansible user for playbook execution")
    parser.add_argument("--private_key_file", type=str, help="Path to the private key file for Ansible")

    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config)

    # Merge config file and command-line arguments
    min_pending_jobs = args.min_pending_jobs or config.get(
        "service", "min_pending_jobs", fallback="1"
    )
    min_pending_jobs = int(min_pending_jobs.split(";")[0].strip())  # Strip inline comments

    settings = {
        "auth_url": args.auth_url or config.get("openstack", "auth_url", fallback=None),
        "project_name": args.project_name or config.get("openstack", "project_name", fallback=None),
        "username": args.username or config.get("openstack", "username", fallback=None),
        "password": args.password or config.get("openstack", "password", fallback=None),
        "user_domain_name": args.user_domain_name or config.get(
            "openstack", "user_domain_name", fallback="default"
        ),
        "project_domain_name": args.project_domain_name or config.get(
            "openstack", "project_domain_name", fallback="default"
        ),
        "vm_flavor": args.vm_flavor or config.get("vm", "flavor", fallback="m1.small"),
        "vm_image": args.vm_image or config.get("vm", "image", fallback="ubuntu-20.04"),
        "vm_network": args.vm_network or config.get("vm", "network", fallback="private"),
        "check_interval": args.check_interval or config.getint(
            "service", "check_interval", fallback=60
        ),
        "min_vms": args.min_vms or config.getint("service", "min_vms", fallback=1),
        "max_vms": args.max_vms or config.getint("service", "max_vms", fallback=10),
        "memory": args.memory or config.getint("slurm", "memory", fallback=80000),
        "feature": args.feature or config.get("slurm", "feature", fallback="f1"),
        "node_config": args.node_config or config.get("slurm", "node_config", fallback=None),
        "cpus": args.cpus or config.getint("slurm", "cpus", fallback=4),
        "vm_name_prefix": args.vm_name_prefix or config.get("vm", "vm_name_prefix", fallback="ecc"),
        "min_pending_jobs": min_pending_jobs,
        "key_name": args.key_name or config.get("vm", "key_name", fallback=None),
        "playbook_path": args.playbook_path or config.get("ansible", "playbook_path", fallback=None),
        "ansible_user": args.ansible_user or config.get("ansible", "ansible_user", fallback=None),
        "private_key_file": args.private_key_file or config.get("ansible", "private_key_file", fallback=None),
    }

    return settings
