#!/usr/bin/env python3

from ryu.cmd.manager import main
from ryu import cfg
import argparse
import sys, os, os.path

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', help="debug mode")
    parser.add_argument('-s', '--stp', action='store_true', help="Enable STP (spanning tree protocol)")
    parser.add_argument('-f', '--file-config', type=str, default='configs/graph4.ini', help="configuration file path (default: configs/graph4.ini)")

    return parser.parse_args()

# Register your custom argument BEFORE parsing
cfg.CONF.register_cli_opts([
    cfg.IntOpt('number_of_switches', default=0, help='Number of switches in the network'),
    cfg.IntOpt('number_of_hosts', default=0, help='Number of hosts in the network'),
    cfg.IntOpt('number_of_links', default=0, help='Number of links in the network'),
    cfg.IntOpt('number_of_slices', default=0, help='Number of slices in the network'),
    cfg.BoolOpt('debug_mode', default=False, help='Enable debug mode'),
    cfg.StrOpt('links_config_host', default="", help='List of slices configuration for hosts'),
    cfg.StrOpt('links_config_switch', default="", help='List of slices configuration for switches'),
    ])

if __name__ == '__main__':

    # Parse command line arguments
    args = parse_args()

    if args.debug:
        print("Debug mode enabled")
        print(args)
    
    # Configure the network topology
    if args.file_config:
        # Read the network topology from a configuration file
        if not os.path.isfile(args.file_config):
            print(f"Configuration file '{args.file_config}' does not exist.")
            sys.exit(1)
            
        # Fill with the configuration arguments from the config file
        from Controller.ReadSlicingTopology import read_config_file
        custom_arg = read_config_file(args.file_config, args.debug)

        # Set the debug mode
        if args.debug:
            custom_arg.append(f'--debug_mode')

        # Remove all existing arguments from sys.argv but keep the script name
        sys.argv = [sys.argv[0]]

        # Select the appropriate Ryu controller script and add the configurations
        path = "Controller/"
        if args.stp:
            sys.argv += [path + 'simple_switch_stp_13.py'] + custom_arg
        else:
            sys.argv += [path + 'simple_switch_13.py'] + custom_arg

        if args.debug:
            print(f"Parameters passed to the sys.argv: {sys.argv}")

        # Launch the Ryu controller with the specified configuration
        main()
