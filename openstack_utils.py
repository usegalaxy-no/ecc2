"""
Utility functions for managing OpenStack VMs.
"""

import base64

def create_vm(conn, name, cloud_init_file, settings):
    """Create a new VM in OpenStack with a cloud-init file."""
    print(f"Creating VM: {name}")
    with open(cloud_init_file, "r", encoding="utf-8") as f:
        user_data = f.read()

    user_data_base64 = base64.b64encode(user_data.encode("utf-8")).decode("utf-8")
    network = conn.network.find_network(settings["vm_network"])
    if not network:
        raise ValueError(f"Network '{settings['vm_network']}' not found in OpenStack.")

    flavor = conn.compute.find_flavor(settings["vm_flavor"])
    if not flavor:
        raise ValueError(f"Flavor '{settings['vm_flavor']}' not found in OpenStack.")

    image = conn.compute.find_image(settings["vm_image"])
    if not image:
        raise ValueError(f"Image '{settings['vm_image']}' not found in OpenStack.")

    if settings["key_name"]:
        keypair = conn.compute.find_keypair(settings["key_name"])
        if not keypair:
            raise ValueError(f"Key pair '{settings['key_name']}' not found in OpenStack.")

    try:
        server = conn.compute.create_server(
            name=name,
            flavor_id=flavor.id,
            image_id=image.id,
            networks=[{"uuid": network.id}],
            user_data=user_data_base64,
        )
        conn.compute.wait_for_server(server)
        server = conn.compute.get_server(server.id)
        if server.status != "ACTIVE":
            raise RuntimeError(f"VM {name} failed to reach 'ACTIVE' state. Current state: {server.status}")
        print(f"VM {name} is in 'ACTIVE' state.")
        return server
    except RuntimeError as e:
        print(f"Error creating VM: {e}")
        raise

def get_running_vms(conn):
    """Get the names of currently running VMs."""
    try:
        servers = conn.compute.servers()
        return [server.name for server in servers if server.status == "ACTIVE"]
    except Exception as e:
        print(f"Error fetching running VMs: {e}")
        return []

def get_next_vm_name(conn, vm_name_prefix, max_vms):
    """Generate the next available VM name."""
    existing_vms = [server.name for server in conn.compute.servers()]
    for i in range(1, max_vms + 1):
        vm_name = f"{vm_name_prefix}-{i}"
        if vm_name not in existing_vms:
            return vm_name
    return None
