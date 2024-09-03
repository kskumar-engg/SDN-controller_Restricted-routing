
# SDN-controller_Restricted-routing

Implement a SDN controller for routing the traffic flows in the given topology. To do this, you will use the OpenFlow Protocol, the Ryu SDN Framework, and the Mininet Network Emulator.

The network topology below comprises three open-flow switches (s1, s2, s3) and six hosts (h1 to h6). The numbers marked over the links represent the respective port numbers of the switches. The goal is to   
a)Create a Ryu SDN controller for enabling below traffic flow rules in the given topology.   
b)Write match rules using IPv4 addresses of hosts not MAC. 

1. h6 to h3 and h6 to h4 traffic should be routed through s1. Backward traffic (i.e., h3/h4 to h6) should follow the same path in reverse order.
2. h5 to h4 traffic should be routed through s1 but h4 to h5 traffic should not be routed through s1.
3. s1 should forward all traffic (except the traffic belonging to rules 1 and 2) for the destinations h4 and h3 to s3.
4. h1 should receive HTTP traffic only.
5. All other traffic flows (not covered by rules 1 to 2) should follow the shortest paths.

## Deployment

**To deploy this project run**

```
ryu-manager --observe-links app.py
sudo python3 topo.py
```

**In mininet:**
```
h6 ping h3
```

In ryu terminal:
you can see path

**To verify flows:**
```
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
```
stop mininet.

**In mininet:**
```
h5 ping h4
```

In ryu you can see forward and return path

Stop mininet:
Do the next ping

You can verify all flows


**Start webserver with**
```
xterm h1
```
**In the h1 window:**
```
python3 -m http.server 80
```
**Verify:**
```
sudo ovs-ofctl -O OpenFlow13 dump-flows s1  
sudo ovs-ofctl -O OpenFlow13 dump-flows s2  
sudo ovs-ofctl -O OpenFlow13 dump-flows s3
```




## Running Tests

To run tests, run the following command



## 1) Run ryu
```
ryu-manager --observe-links app.py
```

## 2) ryn mininet 
```
sudo python3 topo.py
```

## 3) Verify     
  

**Test1:**
```                                        
h6 ping h3
h6 ping h4
```
forward path: [s3, s1, s2]  
reverse path:  [s2, s1, s3]


**Test2:**
```
h5 ping h4
```

forward path: [s3, s1, s2]  
reverse path:  [s2, s3]


**Test3:**
```
h2 ping h3 (or h2 ping h4)
```

forward path [s1, s3, s2]  
reverse parth [ s2, s3]


**Test4:** (h1 only http traffic)
```
xterm h1
python3 -m http.server 80
```
```
h4 curl h1
```
forward path [s2, s3]  
reverse path [ s1, s3, s2]  
   
  
   


**Test5:** any other traffic
```
h6 ping h1
```
