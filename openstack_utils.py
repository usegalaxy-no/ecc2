"""
Utility functions for managing OpenStack VMs.
"""

import base64

def create_vm(conn, name, settings):
    """Create a new VM in OpenStack."""
    print(f"Creating VM: {name}")
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
        if not keypair or keypair.id != settings["key_name"]:
            raise ValueError(f"Key pair '{settings['key_name']}' not found or does not match the expected ID.")

    try:
        server = conn.compute.create_server(
            name=name,
            flavor_id=flavor.id,
            image_id=image.id,
            networks=[{"uuid": network.id}],
            key_name=settings["key_name"],  # Ensure the SSH key is used
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

def get_running_vms(conn, vm_name_prefix=None):
    """Get the names of currently running VMs with an optional prefix filter."""
    try:
        servers = conn.compute.servers()
        running_vms = [server.name for server in servers if server.status == "ACTIVE"]
        if vm_name_prefix:
            running_vms = [vm for vm in running_vms if vm.startswith(vm_name_prefix)]
        return running_vms
    except Exception as e:
        print(f"Error fetching running VMs: {e}")
        return []

def get_next_vm_name(conn, vm_name_prefix, max_vms):
    """Generate the next available VM name."""
    existing_vms = [server.name for server in conn.compute.servers()]
    for i in range(1, max_vms + 1):
        vm_name = f"{vm_name_prefix}{i}"  # Remove the hyphen from the VM name
        if vm_name not in existing_vms:
            return vm_name
    return None
