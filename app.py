from ryu import cfg
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.ofproto import ether
from ryu.lib.packet import ipv4
from ryu.lib.ovs import bridge
from ryu.lib.packet import in_proto
from ryu.lib.packet import ipv4
from ryu.lib.packet import icmp
from ryu.lib.packet import tcp
from ryu.lib.packet import udp
from ryu.lib import hub
import networkx as nx
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link, get_host
import random
from time import sleep

    
DISCOVERY_INERVAL = 20
TOPOLOGY_DISCOVERED = 0

H1_MAC = "00:00:00:00:00:01"
H2_MAC = "00:00:00:00:00:02"
H3_MAC = "00:00:00:00:00:03"
H4_MAC = "00:00:00:00:00:04"
H5_MAC = "00:00:00:00:00:05"
H6_MAC = "00:00:00:00:00:06"


class MPathApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MPathApp, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.mac_to_port = {}
        self.topology_api_app = self
        self.topodiscovery_thread = hub.spawn(self._tdiscovery)    
        self.hosts = []
        self.links = []
        self.switches = []

    def _tdiscovery(self):
        global TOPOLOGY_DISCOVERED
        #while True:
        hub.sleep(DISCOVERY_INERVAL)
        self.get_topology_data()
        TOPOLOGY_DISCOVERED = 1


    def build_topology(self):
        self.networkx = None
        self.networkx = nx.DiGraph()
        for s in self.switches:
            self.networkx.add_node(s, name=s)
        for l in self.links: 
            self.networkx.add_edge(l[0],l[1],weight=1)


    def get_topology_data(self):        
        switch_list = get_switch(self.topology_api_app, None)
        self.switches = [switch.dp.id for switch in switch_list]
        links_list = get_link(self.topology_api_app, None)
        self.links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in links_list]
        host_list = get_host(self.topology_api_app, None)
        self.hosts = [(host.mac, host.port.dpid, {'port': host.port.port_no}) for host in host_list]
        self.logger.info("switches %s", self.switches)
        self.logger.info("links %s", self.links)
        self.logger.info("hosts %s", self.hosts)
        self.build_topology()

    

    def get_dpid(self,mac):
        '''                
        returns the specific host data from the topology discovered hosts
        # host
        #('00:00:00:00:00:01', 10, {'port': 4})
        '''        
        for host in self.hosts:
            if host[0] == mac:
                return host


    def get_portnumber(self,srcdpid,dstdpid):
        for link in self.links:
            if link[0]==srcdpid and link[1]==dstdpid:
                return link[2]["port"]

    def prepareflow(self, dpid, smac, dmac, outport,srcip,dstip):
        datapath = self.datapaths[dpid]
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        #match = parser.OFPMatch(eth_dst=dmac, eth_src=smac,eth_type=ether_types.ETH_TYPE_IP,
        #                        ipv4_src=srcip, ipv4_dst=dstip)


        if dstip == "10.1.0.1":
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                ipv4_src=srcip, ipv4_dst=dstip, ip_proto=6, tcp_dst=80)

            actions = [parser.OFPActionOutput(outport)]
            self.add_flow(datapath, 10, match, actions)            
        else:
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                ipv4_src=srcip, ipv4_dst=dstip )

            actions = [parser.OFPActionOutput(outport)]
            self.add_flow(datapath, 10, match, actions)
        

    def spf_path(self, srcdpid, dstdpid):
        paths = nx.dijkstra_path(self.networkx, srcdpid, dstdpid, weight="weight")
        print("SPF Path is ", paths)
        return paths


    def find_ports(self,pathss):
        ports = []
        for path in pathss:
            srcdpid = path[0] 
            nexthop = path[1]
            pno = self.get_portnumber(srcdpid, nexthop)
            self.logger.info("%d switch-> %d port number %d", srcdpid, nexthop , pno)
            ports.append(pno)
        return ports

    def get_special_path(self, srcmac, dstmac):
        #rule1
        if srcmac == H6_MAC and dstmac in [H3_MAC, H4_MAC]:
            return [ 3, 1, 2]
        if srcmac in [H3_MAC, H4_MAC] and dstmac == H6_MAC:
            return [2, 1, 3]
        #rule2
        if srcmac == H5_MAC and dstmac == H4_MAC:
            return[3, 1, 2]
        #rule3
        if srcmac in [H1_MAC, H2_MAC] and dstmac in [H4_MAC, H3_MAC]:
            return[1, 3, 2]


        return None

    def install_path(self,srcmac,dstmac, srcip, dstip):
        self.logger.info("Caculating PATH from %s to %s" , srcmac , dstmac)
        # Get the Switch connected to Source Host
        result = self.get_dpid(srcmac)
        srcdpid = result[1]
        # Get the Switch connected to Destination Host
        result = self.get_dpid(dstmac)
        dstdpid = result[1]
        dstport = result[2]
        #check whether both srchost and dsthost connected on same switch then return the port
        if srcdpid == dstdpid:
            return dstport['port']


        #apply the filter
        paths = []

        rpath = self.get_special_path(srcmac, dstmac)
        print(rpath)
        if rpath:
            paths = rpath
        else:
            paths = self.spf_path(srcdpid, dstdpid)
        
        self.logger.info("result path is %s",paths)
        #get port number for each path:
        index = 0 #index
        length = len(paths)
        for x in range(0,length-1):
            srcdpid = paths[x]
            nexthop = paths[x+1]
            #self.logger.info('Finding port src %d dst %d ', srcdpid, nexthop)
            port = self.get_portnumber(srcdpid, nexthop)
            #self.logger.info("port %d", port)
            path = {"dpid": srcdpid, "src_mac":srcmac, "dst_mac": dstmac, "port": port}
            #self.logger.info(path)
            self.prepareflow(srcdpid, srcmac, dstmac, port, srcip, dstip)

        # Add a flow in the switch which is connected to the destination host             
        # As this is destination switch, this can be added last(otherwise timing issue of original packetout)
        self.prepareflow(dstdpid, srcmac, dstmac, dstport['port'], srcip, dstip)
        # packet need to send out, hence we need return the immediate next path
        srcdpid = paths[0]
        nexthop = paths[1]
        sleep(0.2)        
        port = self.get_portnumber(srcdpid, nexthop)
        return port
    




    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        self.datapaths[datapath.id] = datapath
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        #self.add_flow(datapath, 0, 0, match, actions)
        self.add_flow(datapath, 0, match, actions,idle_t=0, hard_t=0)



    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_t=5, hard_t=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, idle_timeout=idle_t, hard_timeout=hard_t,
                                    match=match, instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    idle_timeout=idle_t, hard_timeout=hard_t,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)






    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        #self.logger.info("packet in %s src %s dst %s in_port %s type %s", dpid, src, dst, in_port,eth.ethertype)

        #Do not process any packet before topology discovery
        if not TOPOLOGY_DISCOVERED:
            #self.logger.info("Dropping the packet...Topology discovery inprogress")
            return
        
        #DROP BROADCAST and IPv6 MULICAST Packe
        if dst == "ff:ff:ff:ff:ff:ff" or dst[:5] == "33:33":
            #self.logger.info("drop ipv6 multicast packet %s", dst)
            return

        # check IP Protocol and create a match for IP
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ip = pkt.get_protocol(ipv4.ipv4)
            srcip = ip.src
            dstip = ip.dst                        
            oport = self.install_path(src,dst, srcip, dstip)

            if dstip == "10.1.0.1":
                return


            if oport:
                actions = []
                actions.append(parser.OFPActionOutput(oport))
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                                        in_port=in_port, actions=actions, data=msg.data)
                datapath.send_msg(out)            
