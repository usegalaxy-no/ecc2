# OpenStack VM Service with Slurm / ECC

This project automates the creation and management of virtual machines (VMs) in OpenStack and dynamically registers them with a Slurm cluster.

## Features

- Automatically creates VMs in OpenStack based on Slurm job queue and minimum/maximum VM limits.
- Dynamically registers VMs with a Slurm cluster using `slurmd -Z`.
- Supports configuration through a `config.ini` file and command-line arguments.
- Sequentially names VMs with the prefix `ecc*`.

## File Structure

- **`config.py`**: Handles configuration parsing from `config.ini` and command-line arguments.
- **`openstack_utils.py`**: Contains OpenStack-related functions for creating VMs and managing VM names.
- **`main.py`**: The main entry point for the service.
- **`config.ini`**: Configuration file for OpenStack, Slurm, and service settings.

## Prerequisites

1. **Python**: Ensure Python 3.6+ is installed.
2. **Dependencies**: Install required Python packages:
   ```bash
   pip install openstacksdk
   ```
3. **OpenStack Credentials**: Ensure you have valid OpenStack credentials.
4. **Slurm Controller**: Ensure the Slurm controller is configured to accept dynamic node registration.

## Configuration

### `config.ini`

Update the `config.ini` file with your OpenStack and Slurm settings. Example:

```ini
[openstack]
auth_url = http://openstack.example.com:5000/v3
project_name = your_project
username = your_username
password = your_password
user_domain_name = default
project_domain_name = default

[vm]
flavor = m1.small
image = ubuntu-20.04
network = private
min_vms = 1
max_vms = 5
vm_name_prefix = ecc

[service]
check_interval = 60
min_pending_jobs = 1  ; Minimum pending jobs before creating a new VM

[slurm]
memory = 80000
feature = f1
node_config = NodeName=node1 CPUs=16 Boards=1 SocketsPerBoard=1 CoresPerSocket=8 ThreadsPerCore=2 RealMemory=31848
cpus = 16
```

## Usage

1. **Run the Service**:
   ```bash
   python main.py
   ```

2. **Command-Line Arguments**:
   Override configuration values using command-line arguments. Example:
   ```bash
   python main.py --min_vms 2 --max_vms 10 --min_pending_jobs 5
   ```

## How It Works

1. **VM Creation**:
   - The service checks the number of running VMs and pending jobs in the Slurm queue.
   - If the number of running VMs is below the `min_vms` or there are at least `min_pending_jobs` pending jobs, it creates new VMs.

2. **VM Naming**:
   - VMs are named sequentially with the prefix `ecc*` (e.g., `ecc1`, `ecc2`).

3. **Slurm Registration**:
   - Each VM is dynamically registered with the Slurm cluster using `slurmd -Z`.

## Contributing

Feel free to submit issues or pull requests to improve the project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.