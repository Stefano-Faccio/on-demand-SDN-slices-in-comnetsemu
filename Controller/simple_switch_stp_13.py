# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import dpid as dpid_lib
from ryu.lib import stplib
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.app import simple_switch_13
from utilities import *

class SimpleSwitch13(simple_switch_13.SimpleSwitch13):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'stplib': stplib.Stp}

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)

        # Load my configuration options
        load_configuration(self)   
        self.logger.info("\n-------- SimpleSwitch13 WITH STP --------\n")

        self.mac_to_port = {}
        self.stp = kwargs['stplib']

        # Sample of stplib config.
        #  please refer to stplib.Stp.set_config() for details.
        config = {}
        '''dpid_lib.str_to_dpid('0000000000000001'):
                {'bridge': {'priority': 0x8000}},
                dpid_lib.str_to_dpid('0000000000000002'):
                {'bridge': {'priority': 0x9000}},
                dpid_lib.str_to_dpid('0000000000000003'):
                {'bridge': {'priority': 0xa000}}}'''
        self.stp.set_config(config)

    def delete_flow(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        for dst in self.mac_to_port[datapath.id].keys():
            match = parser.OFPMatch(eth_dst=dst)
            mod = parser.OFPFlowMod(
                datapath, command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                priority=1, match=match)
            datapath.send_msg(mod)

    @set_ev_cls(stplib.EventPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        #self.logger.info(f"Packet switch:{dpid} src:{src} dst:{dst} port:{in_port}")

        if eth.dst.startswith("33:33"):
            # Ignore multicast packets
            return


        # ------------- Start of Slice Policy Check -------------

        # Log the packet information if debug mode is enabled
        if self.debug_mode:
            self.logger.info("Packet dpid:%s src:%s dst:%s in_port:%s", dpid, src, dst, in_port)

        #Check if the MAC address belongs to a host in the network.
        mac_src = is_host(self, src)
        mac_dst = is_host(self, dst)

        # Make sure source and destination are hosts
        if mac_src == 0 or mac_dst == 0:
            self.logger.info(f"Packet from {src} to {dst} is not a host, dropping packet")
            return

        # Get the slice information for source and destination MAC addresses
        slice_src = get_slice_host(self, mac_src)
        slice_dst = get_slice_host(self, mac_dst)
        
        # Check if the packet is allowed in the slice
        packet_allowed = slice_src & slice_dst
        self.logger.info(f"Packet H2H src:{src} dst:{dst} - Slice: src={slice_src} dst={slice_dst} -> {'Allowed' if packet_allowed else 'Denied'}")

        if not packet_allowed:
            # Drop the packet: do not forward or learn MAC
            match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)
            self.add_flow(datapath, 1, match, [], msg.buffer_id)
            if self.debug_mode:
                self.logger.info(f"Dropping packet from {src} to {dst} due to slice policy")
            return

        # ------------- End of Slice Policy Check -------------

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(stplib.EventTopologyChange, MAIN_DISPATCHER)
    def _topology_change_handler(self, ev):
        dp = ev.dp
        dpid_str = dpid_lib.dpid_to_str(dp.id)
        msg = 'Receive topology change event. Flush MAC table.'
        self.logger.debug("[dpid=%s] %s", dpid_str, msg)

        if dp.id in self.mac_to_port:
            self.delete_flow(dp)
            del self.mac_to_port[dp.id]

    @set_ev_cls(stplib.EventPortStateChange, MAIN_DISPATCHER)
    def _port_state_change_handler(self, ev):
        dpid_str = dpid_lib.dpid_to_str(ev.dp.id)
        of_state = {stplib.PORT_STATE_DISABLE: 'DISABLE',
                    stplib.PORT_STATE_BLOCK: 'BLOCK',
                    stplib.PORT_STATE_LISTEN: 'LISTEN',
                    stplib.PORT_STATE_LEARN: 'LEARN',
                    stplib.PORT_STATE_FORWARD: 'FORWARD'}
        self.logger.debug("[dpid=%s][port=%d] state=%s",
                          dpid_str, ev.port_no, of_state[ev.port_state])

    def shutdown_link(self, datapath, port_no):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Send a PortMod message to disable the port
        port_mod = parser.OFPPortMod(
            datapath=datapath,
            port_no=port_no,
            hw_addr='00:00:00:00:00:00',  # Set correct MAC address if needed
            config=ofproto.OFPPC_PORT_DOWN,
            mask=ofproto.OFPPC_PORT_DOWN,
            advertise=0
        )
        datapath.send_msg(port_mod)
        self.logger.info("Sent PortMod to disable port %d on switch %s", port_no, datapath.id)
