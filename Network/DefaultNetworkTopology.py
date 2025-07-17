from mininet.topo import Topo

class DefaultNetworkTopology(Topo):
    def __init__(self, topology_type = "home", debug=False):
        # Initialize topology
        Topo.__init__(self)

        if debug:
            print("Creating default topology: " + topology_type)

        # Decide which topology to create
        if topology_type == "home":
            self.__topo_home()
        elif topology_type == "mesh":
            self.__topo_mesh()
        elif topology_type == "garr":
            self.__topo_garr()
        else:
            print("Invalid topology name")

    def __topo_home(self):
        # Create template host, switch, and link
        host_config = dict(inNamespace=True)
        standard_link_config = dict(bw=10)
        backup_link_config = dict(bw=1)
        host_link_config = dict()

        # Create switch nodes
        for i in range(4):
            sconfig = {"dpid": "%016x" % (i + 1)}
            self.addSwitch("s%d" % (i + 1), **sconfig)

        # Create host nodes
        for i in range(5):
            self.addHost("h%d" % (i + 1), **host_config)

        # Add standard switch links
        self.addLink("s1", "s2", **standard_link_config)
        self.addLink("s1", "s3", **standard_link_config)
        #self.addLink("s2", "s3", **standard_link_config)
        self.addLink("s3", "s4", **standard_link_config)
        # Add backup switch links
        #self.addLink("s1", "s2", **backup_link_config)

        # Add host links
        self.addLink("h1", "s1", **host_link_config)
        self.addLink("h2", "s2", **host_link_config)
        self.addLink("h3", "s3", **host_link_config)
        self.addLink("h4", "s4", **host_link_config)
        self.addLink("h5", "s4", **host_link_config)

    def __topo_mesh(self):

        host_config = dict(inNamespace=True)
        standard_link_config = dict(bw=10)
        host_link_config = dict()

        nDevices = 5

        switches = []
        hosts = []

        # Create switch nodes
        for i in range(5):
            sconfig = {"dpid": "%016x" % (i + 1)}
            switches.append(self.addSwitch("s%d" % (i + 1), **sconfig))

        # Create host nodes
        for i in range(5):
            hosts.append(self.addHost("h%d" % (i + 1), **host_config))

        # Add switch links
        for i in range(0, nDevices):
            for j in range(i+1, nDevices):
                self.addLink(switches[i], switches[j], **standard_link_config)

        # Add host links
        for i in range(0, nDevices):
            self.addLink(hosts[i], switches[i], **host_link_config)

    def __topo_garr(self):
        nDevices = 0
