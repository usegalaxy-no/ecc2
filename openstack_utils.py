from openstack import connection
import base64

def create_vm(conn, name, cloud_init_file, settings):
    """Create a new VM in OpenStack with a cloud-init file."""
    print(f"Creating VM: {name}")
    with open(cloud_init_file, "r") as f:
        user_data = f.read()

    # Encode user_data in Base64
    user_data_base64 = base64.b64encode(user_data.encode("utf-8")).decode("utf-8")

    # Find the network UUID based on the name
    network_name = settings["vm_network"]
    network = conn.network.find_network(network_name)
    if not network:
        raise ValueError(f"Network '{network_name}' not found in OpenStack.")

    # Resolve the flavor name to its ID
    flavor_name = settings["vm_flavor"]
    flavor = conn.compute.find_flavor(flavor_name)
    if not flavor:
        raise ValueError(f"Flavor '{flavor_name}' not found in OpenStack.")

    # Resolve the image name to its ID
    image_name = settings["vm_image"]
    image = conn.compute.find_image(image_name)
    if not image:
        raise ValueError(f"Image '{image_name}' not found in OpenStack.")

    server = conn.compute.create_server(
        name=name,
        flavor_id=flavor.id,  # Use the resolved flavor ID
        image_id=image.id,  # Use the resolved image ID
        networks=[{"uuid": network.id}],  # Use the resolved network UUID
        user_data=user_data_base64,  # Pass Base64-encoded user_data
        key_name=settings["key_name"],  # Add the key pair name
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

def get_next_vm_name(conn, vm_name_prefix, max_vms):
    """Generate the next available VM name."""
    existing_vms = [server.name for server in conn.compute.servers()]
    for i in range(1, max_vms + 1):
        vm_name = f"{vm_name_prefix}-{i}"
        if vm_name not in existing_vms:
            return vm_name
    return None
