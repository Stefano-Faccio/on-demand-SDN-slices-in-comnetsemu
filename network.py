#!/usr/bin/env python3

import argparse
import sys, os, os.path

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', help="debug mode")
    parser.add_argument('-c', '--clean', action='store_true', help="clean up")
    parser.add_argument('-f', '--file-config', type=str, default='configs/graph4.ini', help="configuration file path (default: configs/graph4.ini)")

    return parser.parse_args()

if __name__ == '__main__':

    # Check if the script is run with root privileges
    if os.geteuid() != 0:
        print("This script must be run with root privileges.")
        sys.exit(1)

    # Parse command line arguments
    args = parse_args()

    if args.debug:
        print("Debug mode enabled")
        print(args)

    # Clean up any leftovers from previous runs
    if args.clean:
        from mininet.clean import cleanup
        if args.debug:
            print("Cleaning up Mininet... ", end='')
            sys.stdout.flush()
        cleanup()
        if args.debug:
            print("[OK]")
        sys.exit(0)

    # Configure the network topology
    if args.file_config:
        # Read the network topology from a configuration file
        if not os.path.isfile(args.file_config):
            print(f"Configuration file '{args.file_config}' does not exist.")
            sys.exit(1)
            
        from Network.ReadNetworkTopology import ReadNetworkTopology
        topo = ReadNetworkTopology(args.file_config, args.debug)
    else:
        # Use the default network topology
        from Network.DefaultNetworkTopology import DefaultNetworkTopology
        topology_type = "mesh"
        topo = DefaultNetworkTopology(topology_type, args.debug)
    
    # Create the Mininet network with the specified topology
    from mininet.net import Mininet
    from mininet.node import OVSKernelSwitch, RemoteController
    from mininet.cli import CLI
    from mininet.link import TCLink

    net = Mininet(
        topo=topo,
        switch=OVSKernelSwitch,
        build=False,
        autoSetMacs=True,
        autoStaticArp=True,
        link=TCLink,
    )
    # Add a remote controller
    controller = RemoteController("c1", ip="127.0.0.1", port=6633)
    net.addController(controller)

    net.build()
    net.start()
    CLI(net)
    net.stop()