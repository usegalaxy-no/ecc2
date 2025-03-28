from openstack import connection

def create_vm(conn, name, cloud_init_file, settings):
    """Create a new VM in OpenStack with a cloud-init file."""
    print(f"Creating VM: {name}")
    with open(cloud_init_file, "r") as f:
        user_data = f.read()
    server = conn.compute.create_server(
        name=name,
        flavor_id=settings["vm_flavor"],
        image_id=settings["vm_image"],
        networks=[{"uuid": settings["vm_network"]}],
        user_data=user_data,
    )
    conn.compute.wait_for_server(server)
    print(f"VM {name} created successfully.")
    return server

def get_running_vms(conn):
    """Get the names of currently running VMs."""
    try:
        servers = conn.compute.servers()
        return [server.name for server in servers if server.status == "ACTIVE"]
    except Exception as e:
        print(f"Error fetching running VMs: {e}")
        return []

def get_next_vm_name(conn, settings, max_vms):
    """Generate the next sequential VM name."""
    prefix = settings["vm_name_prefix"]
    running_vms = get_running_vms(conn)
    for i in range(1, max_vms + 1):
        vm_name = f"{prefix}-{i}"
        if vm_name not in running_vms:
            return vm_name
    return None  # No available VM names
