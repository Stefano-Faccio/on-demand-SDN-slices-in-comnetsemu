from configparser import ConfigParser
import sys, os, os.path

def read_config_file(file_path, debug):
    config = ConfigParser()
    config.read(file_path)

    try:
        #Get the number of switches, hosts, and links from the config file
        number_of_switches = config.getint('CONFIG', 'number_of_switches')
        number_of_hosts = config.getint('CONFIG', 'number_of_hosts')
        number_of_links = config.getint('CONFIG', 'number_of_links')
        number_of_slices = config.getint('CONFIG', 'number_of_slices')

        links_config_host = [None] * number_of_hosts
        links_config_switch = []
        for i in range(number_of_links):
            link_config = config[f'LINK_{i}']
            slice_info = link_config.get("slice")

            # Make sure slice_info is not None or empty
            if not slice_info or slice_info == "":
                slice_str = " "
            else:
                # Get the slice configuration
                slice = [int(s.strip()) for s in slice_info.split(',')]
                slice_str = ';'.join(map(str, slice))
            
            # Understand if it is H2S or S2S
            node1 = link_config.get("node1")
            node2 = link_config.get("node2")
            s2s = (node1.startswith('s') and node2.startswith('s'))

            if not s2s:
                # H2S case
                if bool(node1.startswith('h')) ^ bool(node2.startswith('h')):
                    host = int(node1[1:]) if node1.startswith('h') else int(node2[1:])
                else:
                    raise ValueError(f"Invalid link configuration for LINK_{i}: {node1} and {node2} must be one host and one switch.")
                links_config_host[i] = slice_str
            else:
                # S2S case
                sw1 = int(node1[1:])
                sw2 = int(node2[1:])
                links_config_switch.append((sw1, sw2, slice_str))

        links_host_str = ','.join(map(str, links_config_host))
        links_switch_str = '#'.join(map(str, links_config_switch))

    except Exception as e:
        print(f"Error reading configuration file: {e}")
        print("Please ensure the configuration file has the correct format and required fields.")
        exit(1)

    if debug:
        print(f"Number of switches: {number_of_switches}")
        print(f"Number of hosts: {number_of_hosts}")
        print(f"Number of links: {number_of_links}")
        print(f"Number of slices: {number_of_slices}")
        print(f"Host link configuration: {links_host_str}")
        print(f"Switch link configuration: {links_switch_str}")
    custom_arg = []
    custom_arg.append(f'--number_of_switches={number_of_switches}')
    custom_arg.append(f'--number_of_hosts={number_of_hosts}')
    custom_arg.append(f'--number_of_links={number_of_links}')
    custom_arg.append(f'--number_of_slices={number_of_slices}')
    custom_arg.append(f'--links_config_host={links_host_str}')
    custom_arg.append(f'--links_config_switch={links_switch_str}')

    return custom_arg


'''
        
            link_config = config[f'LINK_{i}']
            slice = [int(s.strip()) for s in link_config.get("slice").split(',')]
            links_config = slice

        
        
        '''