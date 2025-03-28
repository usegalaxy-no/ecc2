import time
from openstack import connection
from config import parse_config_and_args
from openstack_utils import create_vm, get_running_vms, get_next_vm_name
from slurm_utils import add_vm_to_slurm

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
    while True:
        running_vms = len(get_running_vms(conn))
        print(f"Currently running VMs: {running_vms}")
        if running_vms < settings["min_vms"]:
            print(f"Starting VMs to meet minimum requirement of {settings['min_vms']} VMs.")
            for _ in range(settings["min_vms"] - running_vms):
                vm_name = get_next_vm_name(conn, settings["vm_name_prefix"], settings["max_vms"])
                if not vm_name:
                    print("No available VM names. Maximum VM limit reached.")
                    break
                server = create_vm(conn, vm_name, settings["cloud_init_file"], settings)
                vm_ip = server.access_ipv4  # Adjust based on your OpenStack setup
                add_vm_to_slurm(vm_ip, settings)
        elif running_vms < settings["max_vms"]:
            pending_jobs = get_slurm_queue()
            print(f"Pending jobs: {pending_jobs}")
            if pending_jobs >= settings["min_pending_jobs"]:
                vm_name = get_next_vm_name(conn, settings["vm_name_prefix"], settings["max_vms"])
                if not vm_name:
                    print("No available VM names. Maximum VM limit reached.")
                    break
                server = create_vm(conn, vm_name, settings["cloud_init_file"], settings)
                vm_ip = server.access_ipv4  # Adjust based on your OpenStack setup
                add_vm_to_slurm(vm_ip, settings)
        else:
            print(f"Maximum VM limit of {settings['max_vms']} reached. No new VMs will be created.")
        time.sleep(settings["check_interval"])

if __name__ == "__main__":
    main()
