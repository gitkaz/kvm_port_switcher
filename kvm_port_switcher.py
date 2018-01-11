#!/usr/bin/env python3
# coding: utf-8

# Summaly:
#   This script is "portgroup swithcer". This script can change
#   KVM guest machines interface setting (assigined portgroup) easily.
#
# Limitations:
#   Libvirt can connect various hypervisors, but this script can tareget
#   only libvirt-KVM host and uses portgroup for network setting.
#
# usages:
#   - commandline view mode. domains and interfaces  are shown.
#       kvm_port_swicher.py -c qemu+ssh://(livbirtd_host)
#
#       If you add "-n" argument, then network and portgrouops are shown.
#
#   - commandline set mode.
#       kvm_port_swicher.py -c qemu+ssh://(livbirtd_host) --set -i 5 -p 3
#
#       Set mode, needs -i and -p. This is specify target interface and portgroup.
#       If you add "--dry" argument, then set mode run as "dry-run".
#       No configuration will change.
#
#   - interactive mode.
#       kvm_port_swicher.py -c qemu+ssh://(livbirtd_host) -I
#
#       when use "-I" argument, this script run as interactive.
#       Only -c (--connect) arguement is needed.
#


import sys
import os
import argparse
import xml.etree.ElementTree as ET
import libvirt



def get_nic(target_dom, target_nic_id):
    dom_nics = get_domain_interfaces(target_dom)
    nic = dom_nics[int(target_nic_id)]

    return nic


def interacive_commit_comfirm():
    print("Are you confirm this configuration change?")
    print("")
    input_str = input(">(Y/n)")
    return bool(input_str == "Y")


def interactive_compare(nic_et, new_interface):
    print("If you Commit, following configuration will change.")
    print("")
    show_before_and_after_definition(nic_et, new_interface)


def wait_user_input(max_num):
    input_str = input("Input Number. ([0..%s] Q=Quit) >" % max_num)
    while True:
        if input_str == "Q":
            sys.exit(0)
        if (input_str.isdigit()) and (0 <= int(input_str) <= max_num):
            return int(input_str)
        else:
            print("Input value is wrong.")
            input_str = input("Input Number. ([0..%s] Q=Quit) >" % max_num)


def interactive_choise_portgroup(networks):
    print("Which PortGroup to connect?")
    print("")

    max_num = show_network_and_portgroups(networks) - 1
    input_num = wait_user_input(max_num)
    return input_num


def interactive_choise_nic(domains):
    print("Which Interface choose?")
    print("")

    max_num = show_doms_and_nics(domains) - 1
    input_num = wait_user_input(max_num)
    return input_num


def interactive_mode_end_judge(connection):
    print("If finish this program, turn \"Q\" key.")
    print("Continue this program, turn any other key.")

    finish = input(">")
    if finish == "Q":
        connection.close()
        sys.exit(0)

    os.system("clear")


def interactive_mode(connection, domains, networks):
    os.system("clear")
    print("Enter Interactive Mode.")

    while True:
        input_str = interactive_choise_nic(domains)
        (domain, nic_et) = \
            lookup_dom_and_nic_definition_from_number(domains, input_str)

        if is_domain_active(domain) is True:
            live_DA_permit = confirm_live_detach_and_attach()

        if is_domain_active(domain) is False or live_DA_permit is True:
            os.system("clear")
            input_str = interactive_choise_portgroup(networks)
            (network, portgroup_et) = \
                lookup_network_and_portgroup_definition_from_number(networks, input_str)

            os.system("clear")
            if is_domain_active(domain) is True:
                new_interface = create_interface_definition_live \
                    (nic_et, network, portgroup_et)
            else:
                new_interface = create_interface_definition_static \
                    (nic_et, network, portgroup_et)

            interactive_compare(nic_et, new_interface)

            commit = interacive_commit_comfirm()
            if commit is True:
                update_domain_interface(domain, nic_et, new_interface)

        interactive_mode_end_judge(connection)

    connection = connect_libvirt(args.connect)
    domains = get_all_doms(connection)
    networks = get_all_networks(connection)

    return 0


def live_detach_interface(domain, nic_et):
    update_xml = ET.tostring(nic_et)
    update_xml = update_xml.decode("utf-8")
    result = domain.detachDevice(update_xml)

    return result

def live_attach_interface(domain, nic_et):
    update_xml = ET.tostring(nic_et)
    update_xml = update_xml.decode("utf-8")
    result = domain.attachDevice(update_xml)

    return result

def show_before_and_after_definition(nic_et, new_interface):
    print("Current Configuration\r\n-------------------------")
    ET.dump(nic_et)
    print("Future Configuration\r\n-------------------------")
    ET.dump(new_interface)


def create_interface_definition_live(nic_et, network, portgroup_et):

    new_interface = ET.fromstring("""
    <interface>
    </interface>
    """)
    new_interface.set("type", "network")

    new_network_name = network.name()
    new_portgroup_name = portgroup_et.get("name")

    new_source = ET.fromstring("<source />")
    new_source.set("network", new_network_name)
    new_source.set("portgroup", new_portgroup_name)

    current_mac = nic_et.find("mac")
    current_address = nic_et.find("address")
    current_model = nic_et.find("model")

    new_interface.append(current_mac)
    new_interface.append(new_source)
    new_interface.append(current_model)
    new_interface.append(current_address)

    return new_interface


def live_detach_and_attach(domain, nic_et, new_interface):
    result = live_detach_interface(domain, nic_et)
    result = live_attach_interface(domain, new_interface)

    return result


def create_interface_definition_static(nic_et, network, portgroup_et):

    new_network_name = network.name()
    new_portgroup_name = portgroup_et.get("name")

    new_interface = ET.fromstring(ET.tostring(nic_et))
    new_source = new_interface.find("source")
    new_source.set("network", new_network_name)
    new_source.set("portgroup", new_portgroup_name)

    return new_interface


def update_domain_interface(domain, nic_et, new_interface):

    if is_domain_active(domain) is True:
        result = live_detach_and_attach(domain, nic_et, new_interface)
    else:
        update_xml = ET.tostring(new_interface)
        update_xml = update_xml.decode("utf-8")
        result = domain.updateDeviceFlags(str(update_xml), flags=0)

    if result == 0:
        print("Changed Successfully.")
    elif result == -1:
        print("Change Failure.")

    return result


def is_domain_active(dom):
    return bool(dom.state()[0] == 1)

def confirm_live_detach_and_attach():
    print("Selected dommain is running. Live detach and attach VM interface sometimes DANGEROUS.")
    print("Do you REALLY procced? [Y/n]")
    input_str = input(">")
    return bool(input_str == "Y")


def lookup_network_and_portgroup_definition_from_number(networks, number_str):
    number_specified_by_user = int(number_str)

    i = 0
    for network in networks:
        network_et = get_XML_ETree(network)
        portgroups = network_et.findall("portgroup")
        for portgroup_et in portgroups:
            if number_specified_by_user == i:
                return (network, portgroup_et)
            else:
                i = i+1

    print("User specified portgroup number cannot find.")
    sys.exit(1)


def lookup_dom_and_nic_definition_from_number(domains, number_str):
    number_specified_by_user = int(number_str)

    i = 0
    for domain in domains:
        domain_et = get_XML_ETree(domain)
        devices_et = domain_et.find("devices")
        interfaces = devices_et.findall("interface")
        for interface_et in interfaces:
            if number_specified_by_user == i:
                return (domain, interface_et)
            else:
                i = i+1

    print("User specified interface number cannot find.")
    sys.exit(1)


def print_interfaces_list(list_number, interfaces):
    for i, interface in enumerate(interfaces):
        mac_et = interface.find("mac")
        mac_address = mac_et.get("address")

        source_et = interface.find("source")
        portgroup = source_et.get("portgroup")
        print("  i[%i]: %s (%s) " % (list_number+i, portgroup, mac_address))

    list_number = list_number + len(interfaces)
    return list_number

def print_portgroups_list(list_number, portgroups):
    for i, portgroup in enumerate(portgroups):
        vlans = portgroup.findall("vlan")
        for vlan in vlans:
            vlan_text = ""
            if "trunk" in vlan.attrib and vlan.get("trunk") == "yes":
                vlan_text = "trunk: "

            for tag in vlan.findall("tag"):
                vlan_text = vlan_text + tag.get("id") + " "

            vlan_text = vlan_text.rstrip()

        print("  p[%i]: %s (%s)" % (list_number+i, portgroup.get("name"), vlan_text))

    list_number = list_number + len(portgroups)
    return list_number

def get_domain_interfaces(domain):
    dom_xmlroot = get_XML_ETree(domain)
    devices = dom_xmlroot.find("devices")
    interfaces = []
    for interface in devices.findall("interface"):
        interfaces.append(interface)
    return interfaces


def get_XML_ETree(obj):
    xml = obj.XMLDesc()
    xmlroot = ET.fromstring(xml)
    return xmlroot


def show_doms_and_nics(domains):
    print("--------------------------")
    list_number = 0
    for domain in domains:
        interfaces = get_domain_interfaces(domain)

        if is_domain_active(domain) is True:
            print("domain '%s' (running)" % domain.name())
        else:
            print("domain '%s'" % domain.name())

        list_number = print_interfaces_list(list_number, interfaces)
    print("--------------------------")

    return list_number


def show_network_and_portgroups(networks):
    print("--------------------------")

    list_number = 0
    for network in networks:
        network_xmlroot = get_XML_ETree(network)
        network_name = network_xmlroot.find("name").text
        print("network '%s'" % network_name)

        portgroups = network_xmlroot.findall("portgroup")
        list_number = print_portgroups_list(list_number, portgroups)
    print("--------------------------")

    return list_number


def get_all_doms(connection):
    domains = connection.listAllDomains()

    domain_dic = {}
    for domain in domains:
        domain_dic[domain.name()] = domain

    domains_sorted = []
    for domain_name, domain in sorted(domain_dic.items()):
        domains_sorted.append(domain)

    return domains_sorted



def get_all_networks(connection):
    networks = connection.listNetworks()

    network_dic = {}
    for network_name in networks:
        network = conn.networkLookupByName(network_name)
        network_dic[network_name] = network

    networks_sorted = []
    for network_name, network in sorted(network_dic.items()):
        networks_sorted.append(network)

    return networks_sorted


def connect_libvirt(host):
    connection = libvirt.open(host)
    if connection is None:
        print("Failed to open connection to qemu:///system", file=sys.stderr)
        sys.exit(1)

    print("Connected to libvirt Host.")

    return connection


def commandline_set_mode(domains, networks, args):
    (domain, nic_et) = \
        lookup_dom_and_nic_definition_from_number(domains, args.interface)
    (network, portgroup_et) = \
        lookup_network_and_portgroup_definition_from_number(networks, args.portgroup)

    if is_domain_active(domain) is True:
        if confirm_live_detach_and_attach() == True:
            pass
        else:
            print("Live detach and attach Canceled.")
            sys.exit(0)

        new_interface = create_interface_definition_live \
            (nic_et, network, portgroup_et)
        show_before_and_after_definition(nic_et, new_interface)
    else:
        new_interface = create_interface_definition_static \
            (nic_et, network, portgroup_et)
        show_before_and_after_definition(nic_et, new_interface)

    if args.dry is False:
        if is_domain_active(domain):
            live_detach_and_attach(domain, nic_et, new_interface)
        else:
            update_domain_interface(domain, nic_et, new_interface)

    sys.exit(1)


def check_set_mode(args):
    if args.set is True:
        if args.interface != 0 and args.portgroup != 0:
            return True
        else:
            print("--set needs -i interface and -p portgorup.")
            sys.exit(1)
    else:
        return False


def commandline_mode(domains, networks, args):
    if check_set_mode(args) is True:
        commandline_set_mode(domains, networks, args)
    elif args.network is True:
        show_network_and_portgroups(networks)
    else:
        show_doms_and_nics(domains)

def parse_args():
    parser = argparse.ArgumentParser(description="KVM virtual machine interface switcher")
    parser.add_argument("-c", "--connect", \
                        default='qemu:///system', \
                        help="Hypervisor(libvirtd) connection URI. \
                              default is 'qemu:///system'", \
                        action="store")

    parser.add_argument("-I", "--Interactive", \
                        help="Enable interactive mode", \
                        action="store_true")

    parser.add_argument("-d", "--domain", \
                        help="Show domain and network insterface list of connected hypervisor", \
                        action="store_true")

    parser.add_argument("-n", "--network", \
                        help="Show network and portrgoup list of connected hypervisor", \
                        action="store_true")

    parser.add_argument("-s", "--set", \
                        help="Set mode. This mode configure your hypervisor \
                              configuration. use with -i, -p and --dry.", \
                        action="store_true")

    parser.add_argument("-i", "--interface", \
                        type=int, \
                        help="Specify modify interface by number", \
                        action="store")

    parser.add_argument("-p", "--portgroup", \
                        type=int, \
                        help="Specify target portgroup by number", \
                        action="store", \
                        default=0)

    parser.add_argument("--dry", \
                        help="Don't update real configuration. \
                              Just display before and after Interface XML", \
                        action="store_true")

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    args = parse_args()
    conn = connect_libvirt(args.connect)
    doms = get_all_doms(conn)
    nets = get_all_networks(conn)

    if args.Interactive is True:
        interactive_mode(conn, doms, nets)
    else:
        commandline_mode(doms, nets, args)
