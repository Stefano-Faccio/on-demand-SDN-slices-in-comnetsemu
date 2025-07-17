from ryu import cfg
import sys

# Register configuration options
CONF = cfg.CONF

def load_configuration(self):
    try:
        self.debug_mode = CONF.debug_mode
        self.number_of_switches = CONF.number_of_switches
        self.number_of_hosts = CONF.number_of_hosts
        self.number_of_links = CONF.number_of_links
        self.number_of_slices = CONF.number_of_slices
        self.links_config_host = CONF.links_config_host.split(',') if CONF.links_config_host else []
        self.links_config_switch = CONF.links_config_switch.split('#') if CONF.links_config_switch else []
        # Temp variable to hold switch links
        switch_links = [None] * self.number_of_switches
        for i in range(self.number_of_switches):
            switch_links[i] = set()
        
        for i in range(self.number_of_hosts):
            link_config = self.links_config_host[i].split(';')
            self.links_config_host[i] = set([int(s.strip()) for s in link_config if s.strip().isdigit()])
        
        for i in range(self.number_of_links - self.number_of_hosts):
            (sw1, sw2, link_config) = self.links_config_switch[i].strip("()").split(',')
            link_config = link_config.strip("' ").split(';')
            sw1 = int(sw1)-1
            sw2 = int(sw2)-1
            new_slices = set([int(s.strip()) for s in link_config if s.strip().isdigit()])
            switch_links[sw1].update(new_slices)
            switch_links[sw2].update(new_slices)  # Assuming undirected links

        self.links_config_switch = switch_links
        
    except Exception as e:
        self.logger.error(f"Error reading configuration file: {e}")
        sys.exit(1)

    self.logger.info(f"Number of switches: {self.number_of_switches}")
    self.logger.info(f"Number of hosts: {self.number_of_hosts}")
    self.logger.info(f"Number of links: {self.number_of_links}")
    self.logger.info(f"Number of slices: {self.number_of_slices}")
    self.logger.info(f"Debug mode: {self.debug_mode}")

    self.logger.info(f"Host link configuration:")
    for i, link in enumerate(self.links_config_host):
        self.logger.info(f"  HOST_{i+1}: {link}")

    self.logger.info(f"Switch link configuration:")
    for i, slices in enumerate(self.links_config_switch):
        self.logger.info(f"  SWITCH_{i+1}: {slices}")

# Check if the MAC address belongs to a host in the network.
def is_host(self, mac_address):

    mac_int = int(mac_address.replace(":", ""), 16)
    return mac_int if mac_int <= self.number_of_hosts else 0

def get_slice_host(self, link_id):
    return self.links_config_host[link_id-1]

def get_slice_switch(self, switch_id):
    return self.links_config_switch[switch_id-1]