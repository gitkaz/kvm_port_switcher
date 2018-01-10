# kvm_port_switcher

## Demo Animation
![result](https://github.com/gitkaz/kvm_port_switcher/blob/media/interactive_mode_demo.gif)

## What is this?
This is a Python Script for view and modify KVM guest (domain)'s interface configuration.
This scirpt is able to use either one-shot execution(normal cli command), and continuous interactive interface.

## Limitations.
Server (libvirtd host) should use KVM. And domain interface configuration should based on portgroup.
Like this.
```
<interface type='network'>
  <mac address='ab:cd:ed:01:23:45'/>
  <source network='ovs' portgroup='vlan_10'/>
  <model type='virtio'/>
  <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
</interface>
```
This script can change "**source**" element's attributes(**network** and **portgroup**, only). 

## usage
 - one-shot execute and get domain and interface list.
   - kvm_port_switcher -c "libvirt uri"
 - one-shot execute and get network and porgroup list.
   - kvm_port_switcher -c "libvirt uri" -n
 - one-shot execute and change domain's interfe's network and portgoroup.
   - kvm_port_switcher -c "libvirt uri" --set -i <interface num> -p <portgroup num>
 - interactive mode.
   - kvm_port_switcher -c "libvirt uri" -I

## help
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
