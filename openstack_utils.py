"""
Utility functions for managing OpenStack VMs.
"""

import base64
from openstack import connection

def create_vm(conn, name, cloud_init_file, settings):
    """Create a new VM in OpenStack with a cloud-init file."""
    print(f"Creating VM: {name}")
    with open(cloud_init_file, "r", encoding="utf-8") as f:
        user_data = f.read()

    user_data_base64 = base64.b64encode(user_data.encode("utf-8")).decode("utf-8")
    network_name = settings["vm_network"]
    network = conn.network.find_network(network_name)
    if not network:
        raise ValueError(f"Network '{network_name}' not found in OpenStack.")

    flavor_name = settings["vm_flavor"]
    flavor = conn.compute.find_flavor(flavor_name)
    if not flavor:
        raise ValueError(f"Flavor '{flavor_name}' not found in OpenStack.")

    image_name = settings["vm_image"]
    image = conn.compute.find_image(image_name)
    if not image:
        raise ValueError(f"Image '{image_name}' not found in OpenStack.")

    key_name = settings["key_name"]
    if key_name:
        keypair = conn.compute.find_keypair(key_name)
        if not keypair:
            raise ValueError(f"Key pair '{key_name}' not found in OpenStack.")

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
