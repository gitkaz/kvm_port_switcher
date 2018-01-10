# kvm_port_switcher

### What is this?
Under documentation...


### Usage(--help)
```
usage: kvm_port_switcher.py [-h] -c CONNECT [-I] [-d] [-n] [-s] [-i INTERFACE]
                            [-p PORTGROUP] [--dry]

KVM virtual machine interface switcher

optional arguments:
  -h, --help            show this help message and exit
  -c CONNECT, --connect CONNECT
                        Hypervisor(libvirtd) connection URI. always required.
  -I, --Interactive     Enable interactive mode
  -d, --domain          Show domain(virtual machine) and network insterface
                        list of connected hypervisor
  -n, --network         Show network and portrgoup list of connected
                        hypervisor
  -s, --set             Set mode. This mode configure your hypervisor
                        configuration. use with -i, -p and --dry.
  -i INTERFACE, --interface INTERFACE
                        Specify modify interface by number
  -p PORTGROUP, --portgroup PORTGROUP
                        Specify target portgroup by number
  --dry                 Don't update real configuration. Just display before
                        and after Interface XML
```
