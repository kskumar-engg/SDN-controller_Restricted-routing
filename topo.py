#!/usr/bin/python


from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.node import RemoteController,OVSKernelSwitch
from time import sleep


class Multipahtopo(Topo):
    "Single switch connected to n hosts."

    def build(self):
        s1 = self.addSwitch('s1', cls=OVSKernelSwitch) 
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch) 
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch) 


        h1 = self.addHost('h1', mac="00:00:00:00:00:01", ip="10.1.0.1/8")
        h2 = self.addHost('h2', mac="00:00:00:00:00:02", ip="10.1.0.2/8")
        h3 = self.addHost('h3', mac="00:00:00:00:00:03", ip="10.2.0.3/8")
        h4 = self.addHost('h4', mac="00:00:00:00:00:04", ip="10.2.0.4/8")
        h5 = self.addHost('h5', mac="00:00:00:00:00:05", ip="10.3.0.5/8")
        h6 = self.addHost('h6', mac="00:00:00:00:00:06", ip="10.3.0.6/8")

        #s3 switch
        self.addLink(s3, h6, 1, 1)
        self.addLink(s3, h5, 2, 1)
        self.addLink(s3, s1, 3, 1)
        self.addLink(s3, s2, 4, 1)

        #s1 switch
        self.addLink(s1, h1, 2, 1)
        self.addLink(s1, h2, 3, 1)
        self.addLink(s1, s2, 4, 2)

        #s2 switch
        self.addLink(s2, h3, 3, 1)
        self.addLink(s2, h4, 4, 1)





if __name__ == '__main__':
    setLogLevel('info')
    topo = Multipahtopo()
    c1 = RemoteController('c1', ip='127.0.0.1')
    net = Mininet(topo=topo, controller=c1)
    net.start()
    net.staticArp()

    print("Generating sample ping packets")
    h1 = net.get('h1')
    h2 = net.get('h2')
    h3 = net.get('h3')
    h4 = net.get('h4')
    h5 = net.get('h5')
    h6 = net.get('h6')        
    h1.cmd('ping -c3 10.1.0.2 -W 1 &')
    h2.cmd('ping -c3 10.1.0.1 -W 1 &')
    h3.cmd('ping -c3 10.1.0.1 -W 1 &')
    h4.cmd('ping -c3 10.1.0.1 -W 1 &')    
    h5.cmd('ping -c3 10.1.0.1 -W 1 &')    
    h6.cmd('ping -c3 10.1.0.1 -W 1 &')    


    CLI(net)
    net.stop()
