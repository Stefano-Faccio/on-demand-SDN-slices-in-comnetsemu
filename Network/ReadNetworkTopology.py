from configparser import ConfigParser
from mininet.topo import Topo

class ReadNetworkTopology(Topo):
    def __init__(self, file_path, debug):

        # Initialize topology
        Topo.__init__(self)

        if debug:
            print(f"Reading config topology file {file_path}")

        self.__read_config_file(file_path, debug)

    def __read_config_file(self, file_path, debug):
        config = ConfigParser()
        config.read(file_path)

        try:
            #Get the number of switches, hosts, and links from the config file
            self.number_of_switches = config.getint('CONFIG', 'number_of_switches')
            self.number_of_hosts = config.getint('CONFIG', 'number_of_hosts')
            self.number_of_links = config.getint('CONFIG', 'number_of_links')
            self.convert_names = config.getboolean('CONFIG', 'convert_names', fallback=False)
        except Exception as e:
            print(f"Error reading configuration file: {e}")
            print("Please ensure the configuration file has the correct format and required fields.")
            return []
        
        if debug:
            print(f"Number of switches: {self.number_of_switches}")
            print(f"Number of hosts: {self.number_of_hosts}")
            print(f"Number of links: {self.number_of_links}")
            print(f"Convert names: {self.convert_names}")

        # If convert_names is True, we will use the names from the config file
        # Otherwise, we will use the default names (s1, s2, ..., h1, h2, ...)
        if self.convert_names:
            self.names_map = {}
            for i in range(self.number_of_hosts):
                self.names_map[i+1] = config.get('NAMES', f'{i+1}').lower()
                if debug:
                    print(f"Name {i+1}  -> {self.names_map[i+1]}")

        for i in range(self.number_of_switches):
            sconfig = {"dpid": "%016x" % (i + 1)}
            sconfig['name'] = f"s_{self.names_map[i+1]}" if self.convert_names else f's{i + 1}'
            self.addSwitch(**sconfig)
            if debug:
                print(f"Switch {i+1} -> {sconfig['name']} (dpid: {int(sconfig['dpid'], 16)})")

        for i in range(self.number_of_hosts):
            host_config = dict(inNamespace=True)
            host_config['name'] = f"h_{self.names_map[i+1]}" if self.convert_names else f'h{i + 1}'
            self.addHost(**host_config)
            if debug:
                print(f"Host {i+1} -> {host_config['name']}")

        for i in range(self.number_of_links):
            bandwidth = config.getint(f'LINK_{i}', 'bandwidth')
            node1 = config.get(f'LINK_{i}', 'node1')
            node2 = config.get(f'LINK_{i}', 'node2')
            if self.convert_names:
                node1_name = self.names_map[int(node1[1:])]
                node2_name = self.names_map[int(node2[1:])]
                new_node1 = f"{node1[0]}_{node1_name}"
                new_node2 = f"{node2[0]}_{node2_name}"
                if (node1.startswith('s') and node2.startswith('s')):
                    self.addLink(new_node1, new_node2, bw=bandwidth, intfName=f'{node1_name}-{node2_name}')#, intfName2=f'{node2_name}__{node1_name}
                else:
                    self.addLink(new_node1, new_node2, bw=bandwidth)
            else:
                self.addLink(node1, node2, bw=bandwidth)

            if debug:
                print(f"Link {i+1} -> {node1} <-> {node2} with bandwidth {bandwidth} Mbps")