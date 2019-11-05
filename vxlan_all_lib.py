#!/usr/bin/env python
import re
import pdb
import logging
import time
import pexpect
from time import sleep
import hashlib
import sys
from ipaddress import *
import json
from ats.log.utils import banner
from random import *
from ats.topology import Device
import sth
from sth import StcPython
import requests
from ats import aetest, log
from ats.log.utils import banner
from netaddr import *
from re import *
from randmac import RandMac

#### sep 19
from genie.libs.conf.interface.nxos import Interface
from genie.libs.conf.ospf.nxos.ospf import Ospf
#from genie.libs.conf.rip.rip import Rip
#pkgs/conf-pkg/src/genie/libs/conf/ospf/nxos/ospf.py

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


import general_lib

def SpirentV6BidirStream(port_hdl1,port_hdl2,vlan1,vlan2,scale,ipv61,ipv62,rate_pps):
    log.info(banner("STARTING SpirentV6BidirStream "))
    log.info('VLAN1 : %r,VLAN2 : %r,SCALE : %r,IP1 : %r,IP2 : %r ' ,vlan1,vlan2,scale,ipv61,ipv62)

    device_ret = sth.traffic_config (
        mode            =       'create',
        port_handle     =       port_hdl1,
        l2_encap        =       'ethernet_ii_vlan',
        vlan_id         =       vlan1,
        vlan_id_count   =       scale,
        vlan_id_mode    =       'increment',
        l3_protocol     =       'ipv6',
        ipv6_src_addr   =       ipv61,
        ipv6_src_step   =       '0000:0000:0000:0000:0000:0000:0001:0000',
        ipv6_src_count  =       scale,
        ipv6_src_mode   =       'increment',
        ipv6_dst_addr   =       ipv62,
        ipv6_dst_step   =       '0000:0000:0000:0000:0000:0000:0001:0000',
        ipv6_dst_count  =       scale,
        ipv6_dst_mode   =       'increment',
        mac_src         =       '00:12:60:60:00:02',
        mac_dst         =       '00:13:60:60:00:02',
        mac_src_count   =       scale,
        mac_src_mode    =       'increment',
        mac_src_step    =       '00:00:00:00:00:01',
        mac_dst_count   =       scale,
        mac_dst_mode    =       'increment',
        mac_dst_step    =       '00:00:00:00:00:01',
        rate_pps        =       rate_pps,
        transmit_mode   =       'continuous')

    device_ret = sth.traffic_config (
        mode            =       'create',
        port_handle     =       port_hdl2,
        l2_encap        =       'ethernet_ii_vlan',
        vlan_id         =       vlan2,
        vlan_id_count   =       scale,
        vlan_id_mode    =       'increment',
        l3_protocol     =       'ipv6',
        ipv6_src_addr   =       ipv62,
        ipv6_src_step   =       '0000:0000:0000:0000:0000:0000:0001:0000',
        ipv6_src_count  =       scale,
        ipv6_src_mode   =       'increment',
        ipv6_dst_addr   =       ipv61,
        ipv6_dst_step   =       '0000:0000:0000:0000:0000:0000:0001:0000',
        ipv6_dst_count  =       scale,
        ipv6_dst_mode   =       'increment',
        mac_src         =       '00:13:60:60:00:02',
        mac_dst         =       '00:12:60:60:00:02',
        mac_src_count   =       scale,
        mac_src_mode    =       'increment',
        mac_src_step    =       '00:00:00:00:00:01',
        mac_dst_count   =       scale,
        mac_dst_mode    =       'increment',
        mac_dst_step    =       '00:00:00:00:00:01',
        rate_pps        =       rate_pps,
        transmit_mode   =       'continuous')



def SpirentRateTest22(port_hdl1,port_hdl2,rate_fps,diff):
    log.info(banner("  Starting Spirent Rate Test "))
    diff = 4*int(diff)
    result = 1
    for port_hdl in [port_hdl1,port_hdl2]:
        log.info("port_hdl %r,rate_fps %r,diff is %r", port_hdl,rate_fps,diff)
        res = sth.drv_stats(query_from = port_hdl,properties = "Port.TxTotalFrameRate Port.RxTotalFrameRate")
        rx_rate = res['item0']['PortRxTotalFrameRate']
        tx_rate = res['item0']['PortTxTotalFrameRate']
        log.info('+-----------------------------------------------------------------------+')
        log.info('rx_rate is %r,tx_rate is %r',rx_rate,tx_rate)
        log.info('+-----------------------------------------------------------------------+')
        if abs(int(rx_rate) - int(tx_rate)) > diff:
            log.info('Traffic  Rate Test failed - TX / RX difference is %r',abs(int(rx_rate) - int(tx_rate)))
            log.info('Streamblock is %r',res)
            result = 0
        if abs(int(rx_rate) - int(rate_fps)) > diff:
            log.info('Traffic  Rate Test failed, Rate & FPS diff is %r',abs(int(rx_rate) - int(rate_fps)))
            log.info('Streamblock is %r',res)
            result = 0
    log.info(banner(" Completed Spirent Rate Test "))
    return result


def AllTrafficTest(port_handle1,port_handle2,rate,pps,orphan_handle_list):
    rate3=int(rate)*4
    #diff = 4*int(pps)
    diff = int(rate3*.0125)
    test1=SpirentRateTest22(port_handle1,port_handle2,rate3,diff)

    if not test1:
        log.info(banner("Rate test Failed"))
        return 0

    for port_hdl in orphan_handle_list:
        if port_hdl:
            res = sth.drv_stats(query_from = port_hdl,properties = "Port.TxTotalFrameRate Port.RxTotalFrameRate")
            rx_rate = res['item0']['PortRxTotalFrameRate']
            log.info('+----------------------------------------------------------------------+')
            log.info('+---- Acutual RX rate at Port %r is : %r ------+',port_hdl,rx_rate)
            log.info('+---- Expected RX rate at Port %r is : %r ------+',port_hdl,int(rate)*2)
            log.info('+----------------------------------------------------------------------+')
            if abs(int(rx_rate) - int(rate)*2) > diff:
                log.info('Traffic  Rate Test failed for %r',port_hdl)
                log.info('Stats are %r',res)
                return 0
    return 1


def SpirentRateTestFull(port_list,expected_rate):
    log.info(banner("  Starting Spirent Rate Test : SpirentRateTestFull "))
    log.info('+-----------------------------------------------------------------------+')
    log.info("port_list is  %r, expected_rate is %r",port_list,expected_rate)
    log.info('+-----------------------------------------------------------------------+')

    result = 1
    for port_hdl in port_list:
        log.info("port_hdl %r,rate_fps %r", port_hdl,expected_rate)
        res = sth.drv_stats(query_from = port_hdl,properties = "Port.TxTotalFrameRate Port.RxTotalFrameRate")
        rx_rate = res['item0']['PortRxTotalFrameRate']
        tx_rate = res['item0']['PortTxTotalFrameRate']
        log.info('+-----------------------------------------------------------------------+')
        log.info('rx_rate is %r,tx_rate is %r',rx_rate,tx_rate)
        log.info('+-----------------------------------------------------------------------+')
        if abs(int(rx_rate) - int(tx_rate)) > 50000:
            log.info('Traffic  Rate Test failed - TX / RX difference is %r',abs(int(rx_rate) - int(tx_rate)))
            log.info('Streamblock is %r',res)
            result = 0
        if abs(int(rx_rate) - int(expected_rate)) > 50000:
            log.info('Traffic  Rate Test failed, Rate & FPS diff is %r',abs(int(rx_rate) - int(expected_rate)))
            log.info('Streamblock is %r',res)
            result = 0
    log.info(banner(" Completed Spirent Rate Test "))
    return result


def AllTrafficTestFull(l3_port_list,l3_port_rate,l2_port_rate,\
    l2_port_list,orphan_port_list,orphan_port_rate):
    log.info('+-----------------------------------------------------------------------+')
    log.info("l3_port_list is  %r, l3_port_rate is %r",l3_port_list,l3_port_rate)
    log.info("l2_port_list is  %r, l2_port_rate is %r",l2_port_list,l2_port_rate)
    log.info("Orphan_port_list is  %r, Orphan_port_rate is %r",orphan_port_list,orphan_port_rate)
    log.info('+-----------------------------------------------------------------------+')

    test1=SpirentRateTestFull(l3_port_list,l3_port_rate)
    test2=SpirentRateTestFull(l2_port_list,l2_port_rate)
    test3=SpirentRateTestFull(orphan_port_list,orphan_port_rate)

    if not test1:
        log.info(banner("Rate test Failed for l3_port_list"))
        return 0
    if not test2:
        log.info(banner("Rate test Failed for l2_port_list"))
        return 0
    if not test3:
        log.info(banner("Rate test Failed for orphan_port_list"))
        return 0



def DeviceVxlanPreCleanupAll(uut):
    log.info(banner('Starting DeviceVxlanPreCleanupAll'))

    log.info(banner("Deleteing Monitor session"))
    op = uut.execute('sh run monitor | incl sess')
    if op:
        op1 = op.splitlines()
        for line in op1:
            if 'session' in line:
                try:
                    uut.configure('no {line}'.format(line=line))
                except:
                    log.error('Deleteing Monitor session failed for uut %r',uut)
                    return 0


    log.info(banner("Deleteing PO"))
    op = uut.execute('show interface brief | include Po')
    op1 = op.splitlines()
    po_list=[]
    for line in op1:
        list1 = line.split(" ")
        if 'Po' in list1[0]:
            po_list.append(list1[0])
        po_list = po_list[2:]
        if len(po_list) > 0:
            for po in po_list:
                if not 'port' in po:
                    cfg1 = """#default interface {po}"""
                    cfg2 = """no interface {po}"""
                    try:
                        uut.configure(cfg1.format(po=po))
                        uut.configure(cfg2.format(po=po))
                    except:
                        log.error('Deleteing PO failed for uut %r',uut)
                        return 0


    log.info(banner("Deleteing access lists"))
    op = uut.configure("sh run | incl 'ip access-list'")
    op1 = op.splitlines()
    for line in op1:
        if line:
            if not 'copp' in line:
                if not "sh run |" in line:
                    if "access-list" in line:

                        cfg = "no {line}"
                        try:
                            uut.configure(cfg.format(line=line))
                        except:
                            log.error('Deleteing ACL failed for uut %r',uut)
                            return 0


    log.info(banner("Delete static routes"))
    op = uut.configure("sh run | incl 'ip route '")
    op1 = op.splitlines()
    for line in op1:
        if line:
            if not 'run' in line:
                if not '10.127' in line:
                    if 'ip route ' in line:
                        cfg = "no {line}"

                        try:
                            uut.configure(cfg.format(line=line))
                        except:
                            log.error('Deleteing Static route failed for uut %r',uut)
                            return 0

    log.info(banner("Deleting vrf"))
    op = uut.configure("show vrf")
    op1 = op.splitlines()
    for line in op1:
        if line:
            if not 'default' in line:
                if not 'management' in line:
                    vrf = line.split()[0]
                    try:
                         uut.configure('no vrf context {vrf}'.format(vrf=vrf))
                    except:
                        log.error('Deleteing Static route failed for uut %r',uut)
                        return 0

    log.info(banner("Default Eth interface to L3"))
    op = uut.configure("sh int br | exclu route")
    op1 = op.splitlines()
    for line in op1:
        if line:
            if 'Eth' in line:
                if not 'Ethernet' in line:
                    intf = line.split()[0]
                    cfg = \
                        """
                        default interface {intf}
                        interface {intf}
                        no switchport
                        """
                    try:
                         uut.configure(cfg.format(intf=intf))
                    except:
                        log.error('Default Eth interface to L3 failed for uut %r',uut)
                        return 0

    log.info(banner("Deleting Loopbacks"))
    op = uut.configure("show ip interface brief ")
    op1 = op.splitlines()
    for line in op1:
        if line:
            if 'Lo' in line:
                intf = line.split()[0]

                try:
                     uut.configure('no interface {intf}'.format(intf=intf))
                except:
                    log.error('Deleting Loopbacks failed for uut %r',uut)
                    return 0



    log.info(banner("Deleting community-list"))
    op = uut.execute("show run | incl community-list")
    op1 = op.splitlines()
    for line in op1:
        if not 'run' in line:
            if line:
                if 'community-list' in line:
                    cfg = "no {line}"
                    try:
                        uut.configure(cfg.format(line=line))
                    except:
                        log.error('community-list delete failed in uut',uut)
                        return 0

    log.info(banner("Deleting route-map"))
    op = uut.execute("show run | incl route-map")
    op1 = op.splitlines()
    for line in op1:
        if line:
            if 'route-map' in line:
                if 'permit' in line:
                    cfg = "no {line}"
                    try:
                        uut.configure(cfg.format(line=line))
                    except:
                        log.error('route-map delete failed in uut',uut)
                        return 0
    feature_clean=\
    """
    no feature ngoam
    no feature interface-vlan
    no feature lacp
    no feature tunnel
    show clock
    no feature nv over
    show clock
    no feature bgp
    show clock
    no feature ospf
    show clock
    no feature pim
    no vlan 2-600
    line con
    exec-timeout 0
    line vty
    exec-timeout 0
    show clock
    feature nv over
    show clock
    feature bgp
    show clock
    feature ospf
    show clock
    feature pim
    show clock
    nv overlay evpn
    feature lacp
    feature vn-segment-vlan-based
    feature interface-vlan
    """
    try:
        uut.configure(feature_clean)
    except:
        log.error('feature_clean failed for uut',uut)

    return 1


def SwVxlanPreCleanup(uut):
    log.info(banner("Deleteing adding vxlan features"))

    cmd=\
    """
    no feature nv over
    no feature bgp
    no feature ospf
    no feature pim
    no feature interface-vlan
    no feature bfd
    terminal session-timeout 0
    no vlan 2-3600
    line con
    exec-timeout 0
    line vty
    exec-timeout 0
    feature interface-vlan
    feature lacp
    """
    try:
        uut.configure(cmd)
    except:
        log.error('feature_clean failed for uut in SwVxlanPreCleanup',uut)
        return 0


    log.info(banner("Deleteing access lists"))
    op = uut.configure("sh run | incl 'ip access-list'")
    op1 = op.splitlines()
    for line in op1:
        if line:
            if not 'copp' in line:
                if not "sh run |" in line:
                    if "access-list" in line:
                        cfg = "no {line}"
                        try:
                            uut.configure(cfg.format(line=line))
                        except:
                            log.error('Deleteing ACL failed for uut %r',uut)
                            return 0


    log.info(banner("Delete static routes"))
    op = uut.configure("sh run | incl 'ip route '")
    op1 = op.splitlines()
    for line in op1:
        if line:
            if not 'run' in line:
                if not '10.127' in line:
                    if 'ip route ' in line:
                        cfg = "no {line}"
                        try:
                            uut.configure(cfg.format(line=line))
                        except:
                            log.error('Deleteing Static Route failed for uut %r',uut)
                            return 0


    log.info(banner("Deleting vrf"))
    op = uut.configure("show vrf |  be vxlan")
    op1 = op.splitlines()
    for line in op1:
        if line:
            if not 'default' in line:
                if not 'management' in line:
                    vrf = line.split()[0]


                    try:
                        uut.configure('no vrf context {vrf}'.format(vrf=vrf))
                    except:
                        log.error('Deleteing VRF failed for uut %r',uut)
                        return 0


    log.info(banner("Deleting Port Channels"))

    op = uut.configure("sh run | incl 'interface port-channel'")
    op1 = op.splitlines()
    for line in op1:
        if line:
            if not 'run' in line:
                if not "source" in line:
                    if "port-channel" in line:
                        cfg = "no {line}"

                        try:
                            uut.configure(cfg.format(line=line))
                        except:
                            log.error('Deleteing Po failed for uut %r',uut)
                            return 0


    log.info(banner("Default Eth interface to L3"))
    op = uut.configure("sh int br | exclu route")
    op1 = op.splitlines()
    for line in op1:
        if line:
            if 'Eth' in line:
                if not 'Ethernet' in line:
                    intf = line.split()[0]
                    cfg = \
                        """
                        default interface {intf}
                        interface {intf}
                        no switchport
                        """
                    try:
                        uut.configure(cfg.format(intf=intf))
                    except:
                        log.error('Default Eth interface failed for uut %r',uut)
                        return 0


    log.info(banner("Deleting Loopbacks"))
    op = uut.configure("show ip interface brief ")
    op1 = op.splitlines()
    for line in op1:
        if line:
            if 'Lo' in line:
                intf = line.split()[0]

                try:
                    uuut.configure('no interface {intf}'.format(intf=intf))
                except:
                    log.error('Deleting Loopbacks interface failed for uut %r',uut)
                    return 0



    log.info(banner("Deleting community-list"))
    op = uut.execute("show run | incl community-list")
    op1 = op.splitlines()
    for line in op1:
        if not 'run' in line:
            if line:
                if 'community-list' in line:
                    cfg = "no {line}"
                    try:
                        uut.configure(cfg.format(line=line))
                    except:
                        log.error('community-list delete failed in uut',uut)
                        return 0

    log.info(banner("Deleting route-map"))
    op = uut.execute("show run | incl route-map")
    op1 = op.splitlines()
    for line in op1:
        if line:
            if 'route-map' in line:
                if 'permit' in line:
                    cfg = "no {line}"
                    try:
                        uut.configure(cfg.format(line=line))
                    except:
                        log.error('Deleting route-map failed in uut',uut)
                        return 0




def vxlanL3NodeCommonConfig(uut):
    log.info(banner("Starting vxlanVtepCommonConfig"))
    feature_clean=\
    """
    no feature nv over
    feature nv over
    show clock
    no feature bgp
    feature bgp
    show clock
    no feature ospf
    feature ospf
    show clock
    spanning-tree mode mst
    no spanning-tree mst configuration
    feature lacp
    no ip igmp snooping
    no vlan 2-3831
    system no hap-reset
    nv overlay evpn

    """
    try:
        uut.configure(feature_clean)
    except:
        log.error('Starting vxlanVtepCommonConfig failed in uut',uut)
        return 0



def vxlanVtepIGPConfig(uut,loop0_ip1,loop0_ip2,loop1_ip1,spine_intf_list,pim_rp_address):

    rid = str(loop1_ip1)[:-3]

    cmd=\
            '''
            fabric forwarding anycast-gateway-mac 0000.2222.3333
            feature ospf
            feature pim
            no router ospf 100
            router ospf 100
            router-id {rid}
            ip pim rp-address {pim_rp_address} group-list 224.0.0.0/4
            '''
    try:
        uut.configure(cmd.format(rid=rid,pim_rp_address=pim_rp_address))
    except:
        log.error('OSPF config failed for node',uut)

    log.info(banner("Configureing Loopbacks"))

    if not 'Nil' in loop0_ip2:
        config_str = \
            """
            no interf loopback0
            no interf loopback1
            interf loopback0
            no ip add
            ip add {loop0_ip1}
            ip add {loop0_ip2} second
            ip pim sparse-mode
            descr NVE loopback
            no shut
            ip router ospf 100 area 0.0.0.0
            interf loopback1
            no ip add
            ip add {loop1_ip1}
            descr General_IGP loopback
            no shut
            ip router ospf 100 area 0.0.0.0
            ip pim sparse-mode
            """
        try:
            uut.configure(config_str.format(loop0_ip1=loop0_ip1,loop0_ip2=loop0_ip2,loop1_ip1=loop1_ip1))
        except:
            log.error('Loop Config Failed on UUT',uut)

    else:
        config_str = \
            """
            no interf loopback0
            no interf loopback1
            interf loopback0
            no ip add
            ip add {loop0_ip1}
            ip pim sparse-mode
            descr NVE loopback
            ip router ospf 100 area 0.0.0.0
            no shut
            interf loopback1
            no ip add
            ip add {loop1_ip1}
            descr General_IGP loopback
            no shut
            ip router ospf 100 area 0.0.0.0
            ip pim sparse-mode
            """
        try:
            uut.configure(config_str.format(loop0_ip1=loop0_ip1,loop1_ip1=loop1_ip1))
        except:
            log.error('Loop Config Failed on UUT',uut)


    for intf in spine_intf_list:
        cmd=\
                '''
                default interface {intf}
                interf {intf}
                description VTEP_SPINE
                no switchport
                mtu 9216
                logging event port link-status
                medium p2p
                no ip redirects
                ip unnumbered loopback1
                ip ospf network point-to-point
                ip router ospf 100 area 0.0.0.0
                ip pim sparse-mode
                no shutdown
                '''
        try:
            uut.configure(cmd.format(intf=intf))
        except:
            log.error('Uplink interface config failed for node',uut,intf)





def SwPortChannelconfigs(uut,port_list,vlan_range):
    cmd = """\
    default interface Po101
    default interface Po100
    no int po 101
    no int po 100
    vlan {vlan_range}
    interface po 101
    switchport
    shut
    switchport mode trunk
    switchport trunk allowed vlan {vlan_range}
    spanning-tree bpdufilter enable
    spanning-tree port type edge trunk
    sleep 1
    no shut

    """
    try:
        uut.configure(cmd.format(vlan_range=vlan_range))
    except:
        log.info("Switch TGN Port Configuration Failed")


    cfg = """\
    default interface {intf}
    interface {intf}
    channel-group 101 force mode active
    no shut
    """
    for intf in port_list:
        try:
            uut.configure(cfg.format(intf=intf))
        except:
            log.info("Switch TGN Port Configuration Failed")
            return 0

    return 1


def SviConfigs(uut1,uut2):

    cfg1 = \
    """
    feature interface-vlan
    vlan 10
    no interface vlan10
    interface vlan10
    mtu 9216
    ip pim sparse-mode
    ip address 12.12.1.1/24
    ip router ospf 1 area 0
    no shut
    vlan configuration 10
    ip igmp snooping
    exit
    """
    cfg2 = \
    """
    feature interface-vlan
    vlan 10
    no interface vlan10
    interface vlan10
    mtu 9216
    ip pim sparse-mode
    ip address 12.12.1.2/24
    ip router ospf 1 area 0
    no shut
    vlan configuration 10
    ip igmp snooping
    exit
    """

    try:
        uut1.configure(cfg1)
    except:
        log.info("vTEP L3 SVI for VPC Configuration Failed @ uut %r",uut1)
        return 0

    try:
        uut2.configure(cfg2)
    except:
        log.info("vTEP L3 SVI for VPC Configuration Failed @ uut %r",uut2)
        return 0



def SviConfigsall(uut1,uut2,prefix):

    ip1 = prefix+".1/24"
    ip2 = prefix+".2/24"

    cfg1 = \
    """
    feature interface-vlan
    vlan 10
    no interface vlan10
    interface vlan10
    mtu 9216
    ip pim sparse-mode
    ip address {ip1}
    ip router ospf 100 area 0
    no shut
    vlan configuration 10
    ip igmp snooping
    exit
    """
    cfg2 = \
    """
    feature interface-vlan
    vlan 10
    no interface vlan10
    interface vlan10
    mtu 9216
    ip pim sparse-mode
    ip address {ip2}
    ip router ospf 100 area 0
    no shut
    vlan configuration 10
    ip igmp snooping
    exit
    """

    try:
        uut1.configure(cfg1.format(ip1=ip1))
    except:
        log.info("vTEP L3 SVI for VPC Configuration Failed @ uut %r",uut1)
        return 0

    try:
        uut2.configure(cfg2.format(ip2=ip2))
    except:
        log.info("vTEP L3 SVI for VPC Configuration Failed @ uut %r",uut2)
        return 0

def NvePeerLearningIR(port_handle_list,vlan,uut_list,peer_count):
    log.info(banner(" In NvePeerLearning"))

    for uut in uut_list:
        op1=uut.execute("sh nve peers  | grep nve1 | count")
        if not int(op1) == peer_count:
            log.info("Nve peer check failed for UUT %r",uut)
            uut.execute("sh nve peers")
            return 0

    log.info(banner("NvePeerLearning Passed"))
    return 1



class VPCNodeGlobal(object):
    def __init__(self,node,vpc_domain,peer_ip,mct_mem_list1,src_ip):
        self.node=node
        self.vpc_domain=vpc_domain
        self.peer_ip=peer_ip
        self.mct_mem_list1=mct_mem_list1
        self.peer_ip=peer_ip
        self.src_ip=src_ip

    def vpc_global_conf(self):
        cmd = \
        '''
        spanning-tree mode mst
        no feature vpc
        feature vpc
        feature lacp
        vpc domain {vpc_domain}
        peer-keepalive destination {peer_ip} source {src_ip}
        peer-switch
        ip arp synchronize
        ipv6 nd synchronize
        auto-recovery
        peer-gateway
        '''
        try:
            self.node.configure(cmd.format(peer_ip=self.peer_ip,vpc_domain=self.vpc_domain,src_ip=self.src_ip))
        except:
            log.error('vpc gloabal config failed for node %r',self.node)

        cmd = \
        '''
        interface port-channel {vpc_domain}
        no shut
        switchport
        switchport mode trunk
        spanning-tree port type network
        vpc peer-link
        '''

        try:
            self.node.configure(cmd.format(vpc_domain=self.vpc_domain))
        except:
            log.error('vpc gloabal config failed for node %r',self.node)


        for intf in self.mct_mem_list1:
            cmd = \
                '''
                interface {intf}
                channel-group {vpc_domain} force mode active
                no shut
            '''
            try:
                self.node.configure(cmd.format(intf=intf,vpc_domain=self.vpc_domain))
            except:
                self.node.execute("show port-channel compatibility-parameters")
                log.error('222 vpc_peer_link member conf failed for uut/interface')



def leaf_protocol_check222(uut,protocol_list):
    for proto in protocol_list:
        #result = 1
        if 'ospf' in proto:
            cmd = uut.execute("show ip ospf neighbors | json-pretty")
            if not "addr" in str(cmd):
                log.info('No OSPF neighbor found,Test failed for uut/neighbor')
                return 0
            else:
                test1=json.loads(cmd)
                test11 = test1["TABLE_ctx"]["ROW_ctx"]
                if 'list' in str(type(test11)):
                    neig_list = test11[0]["TABLE_nbr"]["ROW_nbr"]
                    neig_count =  str(neig_list).count('addr')
                    if neig_count == 1:
                        if not 'FULL' in (neig_list)[0]['state']:
                            log.info('OSPF neighbor check failed for uut/neighbor')
                            return 0
                        else:
                            return 1

                    elif neig_count > 1:
                        for i in range(0,neig_count-1):
                            if not 'FULL' in (neig_list)[i]['state']:
                                log.info('OSPF neighbor check failed for uut/neighbor')
                                return 0
                            else:
                                return 1

                else:
                    neig_list= test1["TABLE_ctx"]["ROW_ctx"]["TABLE_nbr"]["ROW_nbr"]
                    neig_count =  str(neig_list).count('addr')
                    if neig_count == 1:
                        if not 'FULL' in (neig_list)['state']:
                            log.info('OSPF neighbor check failed for uut/neighbor')
                            return 0
                        else:
                            return 1

                    elif neig_count > 1:
                        for i in range(0,neig_count-1):
                            if not 'FULL' in (neig_list)[i]['state']:
                                log.info('OSPF neighbor check failed for uut/neighbor')
                                return 0
                            else:
                                return 1


        elif 'bgp' in proto:
            cmd = uut.execute(" show bgp l2 evpn summary | json-pretty")
            if not "state" in str(cmd):
                log.info('No BGP neighbor found,Test failed for uut/neighbor')
                return 0
            else:
                test1=json.loads(cmd)
                test11 = test1["TABLE_vrf"]["ROW_vrf"]
                if 'list' in str(type(test11)):
                    neig_list= test11[0]["TABLE_af"]["ROW_af"][0]["TABLE_saf"][ "ROW_saf"][0]["TABLE_neighbor"]["ROW_neighbor"]
                    neig_count =  str(neig_list).count('neighborid')
                    if neig_count == 1:
                        if not 'Established' in (neig_list)[0]['state']:
                            log.info('BGP neighbor check failed for uut/neighbor')
                            return 0
                        else:
                            return 1

                    elif neig_count > 1:
                        for i in range(0,neig_count-1):
                            if not 'Established' in (neig_list)[i]['state']:
                                log.info('BGP neighbor check failed for uut/neighbor')
                                return 0
                            else:
                                return 1

                else:
                    neig_list= test1["TABLE_vrf"]["ROW_vrf"]["TABLE_af"]["ROW_af"]["TABLE_saf"][ "ROW_saf"]["TABLE_neighbor"]["ROW_neighbor"]
                    neig_count =  str(neig_list).count('neighborid')
                    if neig_count == 1:
                        if not 'Established' in (neig_list)['state']:
                            log.info('BGP neighbor check failed for uut/neighbor')
                            return 0
                        else:
                            return 1

                    elif neig_count > 1:
                        for i in range(0,neig_count-1):
                            if not 'Established' in (neig_list)[i]['state']:
                                log.info('BGP neighbor check failed for uut/neighbor')
                                return 0
                            else:
                                return 1

            log.info('BGP neighbor check passed for uut -------------- :')

        elif 'pim' in protocol_list:
            cmd = uut.execute("show ip pim neighbor | json-pretty ")
            if not "vrf" in str(cmd):
                if not "nbr-add" in str(cmd):
                    log.info('No PIM neighbor found,Test failed for uut/neighbor')
                    return 0
                else:
                    return 1

            elif "vrf" in str(cmd):
                test1=json.loads(cmd)
                test11 = test1["TABLE_vrf"]["ROW_vrf"]
                if 'list' in str(type(test11)):
                    neig_list= test11[0]["TABLE_neighbor"]["ROW_neighbor"]
                    neig_count =  str(neig_list).count('nbr-addr')
                    if neig_count == 1:
                        uptime = (neig_list)[0]['uptime']
                        uptime = uptime.replace(":","")
                        uptime = uptime.replace("d","")
                        uptime = uptime.replace("h","")
                        uptime = uptime.replace("s","")
                        if not int(uptime) > 1:
                            log.info('PIM neighbor check failed for uut/neighbor')
                            return 0
                        else:
                            return 1

                    elif neig_count > 1:
                        for i in range(0,neig_count-1):
                            uptime = (neig_list)[i]['uptime']
                            uptime = uptime.replace(":","")
                            uptime = uptime.replace("d","")
                            uptime = uptime.replace("h","")
                            uptime = uptime.replace("s","")
                            if not int(uptime) > 1:
                                log.info('PIM neighbor check failed for uut/neighbor')
                                return 0
                            else:
                                return 1

                else:
                    neig_list= test1["TABLE_vrf"]["ROW_vrf"]["TABLE_neighbor"]["ROW_neighbor"]
                    neig_count =  str(neig_list).count('nbr-addr')
                    if neig_count == 1:
                        uptime = (neig_list)['uptime']
                        uptime = uptime.replace(":","")
                        uptime = uptime.replace("d","")
                        uptime = uptime.replace("h","")
                        uptime = uptime.replace("s","")
                        if not int(uptime) > 1:
                            log.info('PIM neighbor check failed for uut/neighbor')
                            return 0
                        else:
                            return 1

                    elif neig_count > 1:
                        for i in range(0,neig_count-1):
                            uptime = (neig_list)[i]['uptime']
                            uptime = uptime.replace(":","")
                            uptime = uptime.replace("d","")
                            uptime = uptime.replace("h","")
                            uptime = uptime.replace("s","")
                            if not int(uptime) > 1:
                                log.info('PIM neighbor check failed for uut/neighbor')
                                return 0
                            else:
                                return 1
            else:
                pass

            log.info('PIM Neighbor check passed for uut --------------')

        elif 'nve-peer' in protocol_list:
            #if not 'UnicastBGP' in uut.execute('show nve peers ')
            cmd = uut.execute("show nve peers | json-pretty")
            if not "peer-state" in str(cmd):
                log.info('No NVE neighbor found,Test failed for uut/neighbor,11111')
                time.sleep(20)
                cmd = uut.execute("show nve peers | json-pretty")
                if not "peer-state" in str(cmd):
                    log.info('No NVE neighbor found,Test failed for uut/neighbor,2222')
                    time.sleep(20)
                    cmd = uut.execute("show nve peers | json-pretty")
                    if not "peer-state" in str(cmd):
                        log.info('No NVE neighbor found,Test failed for uut/neighbor,33333')
                        cmd = uut.execute("show nve peers")
                        return 0
            else:
                test1=json.loads(cmd)
                test11 = test1["TABLE_nve_peers"]["ROW_nve_peers"]
                if 'list' in str(type(test11)):
                    neig_list= test11
                    neig_count =  str(neig_list).count('peer-ip')
                    if neig_count == 1:
                        state = (neig_list)[0]['peer-state']
                        if not 'Up' in state:
                            log.info('NVE Peer check failed for uut/neighbor')
                        else:
                            return 1

                    elif neig_count > 1:
                        for i in range(0,neig_count-1):
                            state = (neig_list)[i]['peer-state']
                            if not 'Up' in state:
                                log.info('NVE Peer check failed for uut/neighbor')
                            else:
                                log.info('NVE Peer check passed for uut --------------')
                                return 1


                else:
                    neig_list= test1["TABLE_nve_peers"]["ROW_nve_peers"]
                    neig_count =  str(neig_list).count('peer-ip')
                    if neig_count == 1:
                        state = (neig_list)['peer-state']
                        if not 'Up' in state:
                            log.info('NVE Peer check failed for uut/neighbor')
                        else:
                            return 1

                    elif neig_count > 1:
                        for i in range(0,neig_count-1):
                            state = (neig_list)[i]['peer-state']
                            if not 'Up' in state:
                                log.info('NVE Peer check failed for uut/neighbor')
                            else:
                                log.info('NVE Peer check passed for uut --------------')
                                return 1

        elif 'nve-vni' in protocol_list:
            cmd = uut.execute("show nve vni")
            #test1=json.loads(uut.execute(cmd))
            if not "nve1" in str(cmd):
                log.info('No NVE VNI found,Test failed for uut/neighbor')
                return 0

            if "Down" in str(cmd):
                log.info(' NVE VNI Down,Test failed for uut/neighbor')
                return 0

            else:
                return 1

    log.info('Protocol check passed for uut -------------- :')



def leaf_ibgp_conf(uut,as_number,rid):

    cmd=\
            '''
            feature nv overlay
            nv overlay evpn

            router bgp {as_number}
            router-id {rid}
            graceful-restart restart-time 200
            log-neighbor-changes
            address-family ipv4 unicast
             maximum-paths 32
             maximum-paths ibgp 32
            address-family l2vpn evpn
             maximum-paths ibgp 64
            '''
    try:
        uut.configure(cmd.format(rid=rid,as_number=as_number))
    except:
        log.error('iBGP config failed for uut',uut)

def leaf_neigh_template_conf(uut,as_number,update_src):
    cmd=\
            '''
            router bgp {as_number}
            template peer ibgp-vxlan
             remote-as {as_number}
             update-source {update_src}
             address-family ipv4 unicast
              soft-reconfiguration inbound always
             address-family l2vpn evpn
              send-community
              send-community extended
            '''
    try:
        uut.configure(cmd.format(update_src=update_src,as_number=as_number))
    except:
        log.error('iBGP config failed for uut',uut)

def spine_neigh_template_conf(uut,as_number,update_src,template_name):
    cmd=\
            '''
            router bgp {as_number}
            template peer {name}
            remote-as {as_number}
            update-source {update_src}
            address-family ipv4 unicast
            route-reflector-client
            soft-reconfiguration inbound always
            address-family l2vpn evpn
            send-community
            send-community extended
            route-reflector-client
            '''
    try:
        uut.configure(cmd.format(update_src=update_src,as_number=as_number,name=template_name))
    except:
        log.error('iBGP config failed for uut',uut)


def leaf_neigh_conf(uut,as_number,neigh_list,template_name):
    for neigh in neigh_list:
        cmd=\
            '''
            router bgp {as_number}
            neighbor {neigh}
             inherit peer {name}
            '''
        try:
            uut.configure(cmd.format(as_number=as_number,neigh=neigh,name=template_name))
        except:
            log.error('iBGP config failed for uut',uut)


def leaf_vrf_conf(uut,as_number,vrf_list):
        for vrf in vrf_list:
            cmd=\
            '''
            router bgp {as_number}
            vrf {vrf}
             address-family ipv4 unicast
             advertise l2vpn evpn
            '''
        try:
            uut.configure(cmd.format(as_number=as_number,vrf=vrf))
        except:
            log.error('iBGP config failed for uut',uut)

def ibgp_nwk_adv_conf(uut,as_number,adv_nwk_list):
    for nwk in adv_nwk_list:
        cmd=\
            '''
            router bgp {as_number}
            address-family ipv4 unicast
             network {nwk}
            '''
        try:
            uut.configure(cmd.format(as_number=as_number,nwk=nwk))
        except:
            log.error('iBGP config failed for uut',uut)

class IbgpSpineNode(object):
    def __init__(self,node,rid,as_number,adv_nwk_list,neigh_list,update_src,template_name):
        self.node=node
        self.rid=rid
        self.as_number=as_number
        self.adv_nwk_list=adv_nwk_list
        self.neigh_list=neigh_list
        self.update_src=update_src
        self.template_name=template_name

    def bgp_conf(self):
        leaf_ibgp_conf(self.node,rid=self.rid,as_number=self.as_number)
        if not 'Nil' in self.adv_nwk_list:
            ibgp_nwk_adv_conf(self.node,self.as_number,self.adv_nwk_list)
        spine_neigh_template_conf(self.node,self.as_number,self.update_src,self.template_name)
        leaf_neigh_conf(self.node,self.as_number,self.neigh_list,self.template_name)


class IbgpLeafNode(object):
    def __init__(self,node,rid,as_number,adv_nwk_list,neigh_list,update_src,template_name):
        self.node=node
        self.rid=rid
        self.as_number=as_number
        self.adv_nwk_list=adv_nwk_list
        self.neigh_list=neigh_list
        self.update_src=update_src
        self.template_name=template_name

    def bgp_conf(self):
        leaf_ibgp_conf(self.node,rid=self.rid,as_number=self.as_number)
        leaf_neigh_template_conf(self.node,self.as_number,self.update_src)
        leaf_neigh_conf(self.node,self.as_number,self.neigh_list,self.template_name)
        if not 'Nil' in self.adv_nwk_list:
            ibgp_nwk_adv_conf(self.node,self.as_number,self.adv_nwk_list)




def spine_ibgp_conf(uut,as_number,rid,adv_nwk_list,update_src,neigh_list):
    cmd=\
            '''
            feature nv overlay
            nv overlay evpn

            router bgp {as_number}
            router-id {rid}
            graceful-restart restart-time 200
            log-neighbor-changes
            address-family ipv4 unicast
            address-family l2vpn evpn
            maximum-paths 64
            maximum-paths ibgp 64

            '''
    try:
        uut.configure(cmd.format(rid=rid,as_number=as_number,update_src=update_src))
    except:
        log.error('iBGP config failed for uut',uut)

    for neigh in neigh_list:
        cmd=\
            '''
            router bgp {as_number}
            neighbor {neigh}
            inherit peer ibgp-vxlan
            '''
    try:
        uut.configure(cmd.format(neigh=neigh,as_number=as_number))
    except:
        log.error('iBGP config failed for uut',uut)


    for nwk in adv_nwk_list:
        cmd=\
            '''
            router bgp {as_number}
            address-family ipv4 unicast
             network {nwk}
            '''
        try:
            uut.configure(cmd.format(as_number=as_number,nwk=nwk))
        except:
            log.error('iBGP config failed for uut',uut)

######
def vrf_configure(uut,routed_vni,count):
    cmd=""
    for i in range(0,count):
        cmd +=  'vrf context vxlan-{routed_vni}\n'.format(routed_vni=routed_vni)
        cmd +=  'vni {routed_vni}\n'.format(routed_vni=routed_vni)
        cmd +=  'rd auto\n'
        cmd +=  'address-family ipv4 unicast\n'
        cmd +=  'route-target import 1000:{routed_vni} \n'.format(routed_vni=routed_vni)
        cmd +=  'route-target import 1000:{routed_vni} evpn \n'.format(routed_vni=routed_vni)
        cmd +=  'route-target export 1000:{routed_vni} \n'.format(routed_vni=routed_vni)
        cmd +=  'route-target export 1000:{routed_vni} evpn \n'.format(routed_vni=routed_vni)
        cmd +=  'address-family ipv6 unicast\n'
        cmd +=  'route-target import 1000:{routed_vni} \n'.format(routed_vni=routed_vni)
        cmd +=  'route-target import 1000:{routed_vni} evpn\n'.format(routed_vni=routed_vni)
        cmd +=  'route-target export 1000:{routed_vni}\n'.format(routed_vni=routed_vni)
        cmd +=  'route-target export 1000:{routed_vni} evpn\n'.format(routed_vni=routed_vni)
        routed_vni = routed_vni + 1
    try:
        uut.configure(cmd)
    except:
        log.error('vrf configure failed for')


def vlan_vni_configure(uut,vlan,vni,count):
    cmd=""
    for vlan,vni in zip(range(vlan,vlan+count),range(vni,vni+count)):
        #log.info('vlan ----------------- is %r vni is ----------------%r',vlan,vni)
        cmd +=  'vlan {vlan}\n'.format(vlan=vlan)
        cmd +=  'vn-segment {vni}\n'.format(vni=vni)
    try:
        uut.configure(cmd)
    except:
        log.error('vni/vlan configure failed for uut')


def vlan_vni_remove(uut,vlan,vni,count):
    for vlan,vni in zip(range(vlan,vlan+count+1),range(vni,vni+count+1)):
        log.info('vlan ----------------- is %r vni is ----------------%r',vlan,vni)
        cmd = \
            '''
            vlan {vlan}
            no vn-segment {vni}
            '''
        try:
            uut.configure(cmd.format(vni=vni,vlan=vlan))
        except:
            log.error('vni/vlan configure failed for uut',uut,'vlan/vni',vlan,vni)


def vlan_remove(uut,vlan,count):
    for vlan in range(vlan,vlan+count+1):
        log.info('vlan ----------------- is %r vni is ----------------%r',vlan,vni)
        cmd = \
            '''
             no vlan {vlan}
            '''
        try:
            uut.configure(cmd.format(vlan=vlan))
        except:
            log.error('vlan remove configure failed')



def routed_svi_configure(uut,routed_vlan,routed_vni,count):
    cmd = ""
    for i in range(0,count):
        cmd += 'no interface Vlan{routed_vlan}\n'.format(routed_vlan=routed_vlan)
        cmd += 'interface Vlan{routed_vlan}\n'.format(routed_vlan=routed_vlan)
        cmd += 'no shutdown\n'
        cmd += 'mtu 9216\n'
        cmd += 'vrf member vxlan-{routed_vni}\n'.format(routed_vni=routed_vni)
        cmd += 'no ip redirects\n'
        cmd += 'no ipv6 redirects\n'
        cmd += 'ip forward\n'
        cmd += 'ipv6 forward\n'
        routed_vni = routed_vni + 1
        routed_vlan = routed_vlan + 1
    try:
        uut.configure(cmd)
    except:
        log.error('Routed SVI configure failed for uut')



def ConnectSpirent(labserver_ip,tgn_ip,port_list):
    """ function to configure vpc """
    logger.info(banner("Entering proc to connect to Spirent"))
    try:
        lab_svr_sess = sth.labserver_connect(server_ip =labserver_ip,create_new_session = 1, session_name = "Stc",user_name = "danthoma")
        intStatus = sth.connect(device=tgn_ip, port_list = port_list,break_locks = 1, offline = 0 )
        #(' intStatus', {'status': '1', 'offline': '0', 'port_handle': {'10.127.62.251': {'1/7': 'port1', '1/4': 'port2'}}})
        #print("intStatus",intStatus)
        status=intStatus['status']
        if (status == '1') :
            spirent_port_handle=intStatus['port_handle'][tgn_ip]
            log.info("port_handle is %r",spirent_port_handle)
            return spirent_port_handle
        else :
            log.info('\nFailed to retrieve port handle!\n')
            return (0, tgn_port_dict)
    except:

        log.error('Spirect connection failed')
        log.error(sys.exc_info())


def svi_configure(uut,vlan,vlan_scale,ipv4_add,ipv6_add,routed_vni,routed_vni_scale):
    v4 = ip_address(ipv4_add)
    v6 = IPv6Address(ipv6_add)
    c2 = int(vlan_scale/routed_vni_scale)
    cmd = " "
    for j in range(0,routed_vni_scale):  # 5
        for i in range(0,c2):
            v4 = v4 + 65536
            v6 = v6 + 65536
            v4add = v4 + 1
            v6add = v6 + 1
            cmd += 'no interface Vlan{vlan}\n'.format(vlan=vlan)
            cmd += 'interface Vlan{vlan}\n'.format(vlan=vlan)
            cmd += 'no shutdown\n'
            cmd += 'mtu 9216\n'
            cmd += 'vrf member vxlan-{routed_vni}\n'.format(routed_vni=routed_vni)
            cmd += 'no ip redirects\n'
            cmd += 'ip address {v4add}/16\n'.format(v4add=v4add)
            cmd += 'ipv6 address {v6add}/112\n'.format(v6add=v6add)
            cmd += 'no ipv6 redirects\n'
            cmd += 'fabric forwarding mode anycast-gateway\n'
            vlan = vlan + 1
        routed_vni = routed_vni + 1
    try:
        uut.configure(cmd)
    except:
        log.error('SVI configure failed for vlan')



def nve_configure_bgp(uut,vni,count):

    cmd1 = \
    """
    interface nve1
    no shutdown
    host-reachability protocol bgp
    source-interface loopback0
    source-interface hold-down-time 250
    """
    uut.configure(cmd1)
    c1 = int(count/2)-1
    vni1 = vni
    vni2 = vni1 + c1
    cmd = " "
    cmd += 'interface nve1\n'
    for vni in range(vni1,vni2+1):
        cmd += 'member vni {vni}\n'.format(vni=vni)
        cmd += 'suppress-arp\n'
        cmd += 'ingress-replication protocol bgp\n'

    try:
        uut.configure(cmd)
    except:
        log.info('vni_configure failed for uut %r',uut)


def nve_configure_mcast222(uut,vni,count,mcast_group,mcast_group_scale):
    cmd = \
            '''
            interface nve1
            no shutdown
            host-reachability protocol bgp

            source-interface loopback0
            source-interface hold-down-time 250
            '''
    try:
        uut.configure(cmd)
    except:
        log.error('vni_configure failed for uut',uut)

    c1 = int(count/2)
    vni = vni + c1
    c2 = int(c1/mcast_group_scale)
    mcast = ip_address(mcast_group)
    cmd= " "
    cmd += 'interface nve1\n'
    for j in range(0,mcast_group_scale):
        mcast = mcast+1
        for i in range(0,c2):
            cmd += 'member vni {vni}\n'.format(vni=vni)
            cmd += 'suppress-arp\n'
            cmd += 'mcast-group {mcast}\n'.format(mcast=mcast)
            vni = vni + 1

    try:
        uut.configure(cmd)
    except:
        log.error('routed_vni_configure failed for mcast/vni')



def nve_configure_only_mcast(uut,vni,count,mcast_group):
    cmd1 = \
            '''
            interface nve1
            no shutdown
            host-reachability protocol bgp

            source-interface loopback0
            source-interface hold-down-time 250
            '''
    try:
        uut.configure(cmd1)
    except:
        log.info('vni_configure failed for uut %r',uut)

    if int(count)>500:
        c2 = int(count/20)
        a1 = 20
    else:
        c2 = int(count/4)
        a1 = 4
    mcast = ip_address(mcast_group)
    cmd = ""
    cmd +=  'interface nve1\n'
    for j in range(0,a1):
        mcast = mcast+1
        for i in range(0,c2):
            cmd += 'member vni {vni}\n'.format(vni=vni)
            cmd += 'suppress-arp\n'
            cmd += 'mcast-group {mcast}\n'.format(mcast=mcast)
            vni = vni + 1
    try:
        uut.configure(cmd)
    except:
        log.info('mcast_vni_configure failed')

def nve_configure_only_bgp(uut,vni,count):
    cmd1 = \
            '''
            no interface nve1
            interface nve1
            no shutdown
            host-reachability protocol bgp

            source-interface loopback0
            source-interface hold-down-time 250
            '''
    try:
        uut.configure(cmd1)
    except:
        log.info('vni_configure failed for uut %r',uut)

    vni1 = vni
    vni2 = vni1 + count - 1
    cmd = " "
    cmd += 'interface nve1\n'
    for vni in range(vni1,vni2+1):
        cmd += 'member vni {vni}\n'.format(vni=vni)
        cmd += 'suppress-arp\n'
        cmd += 'ingress-replication protocol bgp\n'
    try:
        uut.configure(cmd.format(vni1=vni1,vni2=vni2))
    except:
        log.error('vni_configure failed for uut %r',uut)


def routed_nve_configure(uut,routed_vni,count):
    cmd = " "
    cmd += 'interface nve1\n'
    for i in range(0,count):
        cmd += 'member vni {routed_vni} associate-vrf\n'.format(routed_vni=routed_vni)
        routed_vni = routed_vni + 1
    try:
        uut.configure(cmd)
    except:
        log.error('routed_vni_configure failed for uut',uut,'vlan/vni',routed_vni)


def evpn_vni_configure(uut,vni,count):
    cmd = ""
    cmd +=  'evpn\n'
    for i in range(0,count):
        cmd += 'vni {vni} l2\n'.format(vni=vni)
        cmd += 'rd auto\n'
        cmd += 'route-target import auto\n'
        cmd += 'route-target export auto\n'
        vni = vni + 1
    try:
        uut.configure(cmd)
    except:
        log.error('vni/vlan configure failed for uut ')



def vrf_bgp_configure(uut,as_number,routed_vni,count):
    print("Count issss",count)
    for i in range(0,count):

        #print(routed_vni)
        cmd = \
            '''
            router bgp {as_number}
            vrf vxlan-{routed_vni}
              graceful-restart restart-time 300
              address-family ipv4 unicast
                advertise l2vpn evpn
              address-family ipv6 unicast
               advertise l2vpn evpn
            '''
        #print(cmd.format(routed_vni=routed_vni,as_number=as_number))
        try:
            uut.configure(cmd.format(routed_vni=routed_vni,as_number=as_number))
        except:
            log.error('vni/vlan configure failed for uut %r vni %r',uut,routed_vni)

        routed_vni = routed_vni + 1



class LeafObject2222(object):
    def __init__(self,node,vlan,vni,vlan_scale,routed_vlan,routed_vni,routed_vni_scale,\
    ipv4_add,ipv6_add,mcast_group,as_number,ir_mode,mcast_group_scale):
        self.node=node
        self.vlan=vlan
        self.vni=vni
        self.vlan_scale=vlan_scale
        self.routed_vlan=routed_vlan
        self.routed_vni=routed_vni
        self.routed_vni_scale=routed_vni_scale
        self.ipv4_add=ipv4_add
        self.ipv6_add=ipv6_add
        self.mcast_group=mcast_group
        self.as_number=as_number
        self.ir_mode=ir_mode
        self.mcast_group_scale=mcast_group_scale

        #ir_mode = bgp,mcast,mix

    def vxlan_conf(self):

        vrf_configure(self.node,self.routed_vni,self.routed_vni_scale)
        vlan_vni_configure(self.node,self.routed_vlan,self.routed_vni,self.routed_vni_scale)
        vlan_vni_configure(self.node,self.vlan,self.vni,self.vlan_scale)
        routed_svi_configure(self.node,self.routed_vlan,self.routed_vni,self.routed_vni_scale)
        svi_configure(self.node,self.vlan,self.vlan_scale,self.ipv4_add,self.ipv6_add,self.routed_vni,self.routed_vni_scale)

        if 'mix' in self.ir_mode:
            log.info(banner("Replication mode is BGP + MCAST"))
            nve_configure_bgp(self.node,self.vni,self.vlan_scale)
            nve_configure_mcast222(self.node,self.vni,self.vlan_scale,self.mcast_group,self.mcast_group_scale)
        elif 'bgp' in self.ir_mode:
            log.info(banner("Replication mode is BGP"))
            nve_configure_only_bgp(self.node,self.vni,self.vlan_scale)
        elif 'mcast' in self.ir_mode:
            log.info(banner("Replication mode is MCAST"))
            nve_configure_only_mcast(self.node,self.vni,self.vlan_scale,self.mcast_group)

        routed_nve_configure(self.node,self.routed_vni,self.routed_vni_scale)
        evpn_vni_configure(self.node,self.vni,self.vlan_scale)
        vrf_bgp_configure(self.node,self.as_number,self.routed_vni,self.routed_vni_scale)


class LeafObjectL2(object):
    def __init__(self,node,vlan,vni,vlan_scale,\
    mcast_group,ir_mode,mcast_group_scale):
        self.node=node
        self.vlan=vlan
        self.vni=vni
        self.vlan_scale=vlan_scale
        self.mcast_group=mcast_group
        self.ir_mode=ir_mode
        self.mcast_group_scale=mcast_group_scale

        #ir_mode = bgp,mcast,mix

    def vxlan_conf(self):
        vlan_vni_configure(self.node,self.vlan,self.vni,self.vlan_scale)

        if 'mix' in self.ir_mode:
            log.info(banner("Replication mode is BGP + MCAST"))
            nve_configure_bgp(self.node,self.vni,self.vlan_scale)
            nve_configure_mcast222(self.node,self.vni,self.vlan_scale,self.mcast_group,self.mcast_group_scale)
        elif 'bgp' in self.ir_mode:
            log.info(banner("Replication mode is BGP"))
            nve_configure_only_bgp(self.node,self.vni,self.vlan_scale)
        elif 'mcast' in self.ir_mode:
            log.info(banner("Replication mode is MCAST"))
            nve_configure_only_mcast(self.node,self.vni,self.vlan_scale,self.mcast_group)
        evpn_vni_configure(self.node,self.vni,self.vlan_scale)






def ArpTrafficGenerator2(port_handle,vlan,ip_sa,ip_da,mac_sa,rate_pps,count):

    log.info("port_handle %r vlan %r ip_sa %r ip_da %r mac_sa %r ",port_handle,vlan,ip_sa,ip_da,mac_sa)
    streamblock_ret1 = sth.traffic_config (
        mode = 'create',
        port_handle = port_handle,
        l2_encap = 'ethernet_ii_vlan',
        vlan_id=vlan,
        l3_protocol = 'arp',
        ip_src_addr = ip_sa,
        ip_src_count = count,
        ip_src_mode = 'increment',
        ip_src_step ='0.0.0.1',
        ip_dst_addr = ip_da,
        ip_dst_count = count,
        ip_dst_mode = 'increment',
        ip_dst_step ='0.0.0.1',
        arp_src_hw_addr = mac_sa,
        arp_src_hw_mode = 'increment',
        arp_src_hw_count = count,
        arp_dst_hw_addr = "00:00:00:00:00:00",
        arp_dst_hw_mode = "fixed",
        arp_operation = "arpRequest",
        rate_pps = rate_pps,
        mac_src = mac_sa,
        mac_dst = 'ff:ff:ff:ff:ff:ff',
        mac_src_count= count,
        mac_src_mode='increment',
        mac_src_step='00:00:00:00:00:01',
        transmit_mode = 'continuous')

    status = streamblock_ret1['status']


def VxlanStArpGen(port_handle_list,vlan,ip_sa,ip_da,mac_sa,rate_pps,count):
    log.info(banner("Starting VxlanStArpGen"))

    for port_hdl in  port_handle_list:
        log.info("Resetting all Streams for Port %r",port_hdl)
        traffic_ctrl_ret = sth.traffic_control(port_handle = port_hdl, action = 'reset')


    ip_sa1 = ip_address(ip_sa)
    ip_da1 = ip_address(ip_da)
    mac_sa1 = EUI(mac_sa)

    for port_hdl in  port_handle_list:
        log.info("Adding ARP Stream for Port %r",port_hdl)
        ArpTrafficGenerator2(port_hdl,vlan,str(ip_sa1),str(ip_da1),str(mac_sa1),rate_pps,count)
        mac_sa2 = int(mac_sa1)+1
        mac_sa1 = EUI(mac_sa2)
        ip_sa1 =  ip_sa1+1
        ip_da1 =  ip_da1

    for port_hdl in  port_handle_list:
        log.info("Starting ARP Stream Traffic for Port %r",port_hdl)
        traffic_ctrl_ret = sth.traffic_control(port_handle = port_hdl, action = 'run')

    log.info(banner("Starting ARP for all streams"))
    for i in range(1,4):
        doarp = sth.arp_control(arp_target='allstream',arpnd_report_retrieve='1')



def FloodTrafficGeneratorScale(port_handle,vlan,ip_sa,ip_da,rate_pps,count):

    log.info(banner('in FloodTrafficGeneratorScale '))

    str1=hex(randint(16,54))[2:]
    str2=hex(randint(55,104))[2:]
    str3=hex(randint(32,80))[2:]
    str4=hex(randint(50,95))[2:]

    mac1='00:'+str4+':'+str2+':'+str1+':'+str3+':02'
    #mac2='00:10:'+str1+':'+str2+':'+str4+':02'

    device_ret = sth.traffic_config (
        mode            =       'create',
        port_handle     =       port_handle,
        l2_encap        =       'ethernet_ii_vlan',
        vlan_id         =       vlan,
        vlan_id_count   =       count,
        vlan_id_mode    =       'increment',
        l3_protocol     =       'ipv4',
        ip_src_addr     =       ip_sa,
        ip_src_step     =       '0.1.0.0',
        ip_src_count    =       count,
        ip_src_mode     =       'increment',
        ip_dst_addr     =       ip_da,
        mac_dst         =       'ff:ff:ff:ff:ff:ff',
        mac_src         =       mac1,
        mac_src_count   =       count,
        mac_src_mode    =       'increment',
        rate_pps        =       rate_pps,
        transmit_mode   =       'continuous')

    status = device_ret['status']
    if (status == '0') :
        log.info("run sth.emulation_device_config failed")
        return 0
    else:
        log.info("***** run sth.emulation_device_config successfully")
        return 1


def SpirentBidirStream222(port_hdl1,port_hdl2,vlan1,vlan2,scale,ip1,ip2,gw1,gw2,rate_pps):
    #log.info(banner("------SpirentHostBidirStream-----"))
    log.info('VLAN1 : %r,VLAN2 : %r,SCALE : %r,IP1 : %r,IP2 : %r GW1 :%r GW2 :%r' ,vlan1,vlan2,scale,ip1,ip2,gw1,gw2)

    device_ret = sth.traffic_config (
        mode            =       'create',
        port_handle     =       port_hdl1,
        l2_encap        =       'ethernet_ii_vlan',
        vlan_id         =       vlan1,
        vlan_id_count   =       scale,
        vlan_id_mode    =       'increment',
        l3_protocol     =       'ipv4',
        ip_src_addr     =       ip1,
        ip_src_step     =       '0.1.0.0',
        ip_src_count    =       scale,
        ip_src_mode     =       'increment',
        ip_dst_addr     =       ip2,
        ip_dst_step     =       '0.1.0.0',
        ip_dst_count    =       scale,
        ip_dst_mode     =       'increment',
        mac_src         =       '00:12:94:aa:00:02',
        mac_dst         =       '00:13:94:bb:00:02',
        mac_src_count   =       scale,
        mac_src_mode    =       'increment',
        mac_src_step    =       '00:00:00:00:00:01',
        mac_dst_count   =       scale,
        mac_dst_mode    =       'increment',
        mac_dst_step    =       '00:00:00:00:00:01',
        rate_pps        =       rate_pps,
        transmit_mode   =       'continuous')

    device_ret = sth.traffic_config (
        mode            =       'create',
        port_handle     =       port_hdl2,
        l2_encap        =       'ethernet_ii_vlan',
        vlan_id         =       vlan1,
        vlan_id_count   =       scale,
        vlan_id_mode    =       'increment',
        l3_protocol     =       'ipv4',
        ip_src_addr     =       ip2,
        ip_src_step     =       '0.1.0.0',
        ip_src_count    =       scale,
        ip_src_mode     =       'increment',
        ip_dst_addr     =       ip1,
        ip_dst_step     =       '0.1.0.0',
        ip_dst_count    =       scale,
        ip_dst_mode     =       'increment',
        mac_src         =       '00:13:94:bb:00:02',
        mac_dst         =       '00:12:94:aa:00:02',
        mac_src_count   =       scale,
        mac_src_mode    =       'increment',
        mac_src_step    =       '00:00:00:00:00:01',
        mac_dst_count   =       scale,
        mac_dst_mode    =       'increment',
        mac_dst_step    =       '00:00:00:00:00:01',
        rate_pps        =       rate_pps,
        transmit_mode   =       'continuous')



def SpirentRoutedBidirStream(uut,port_hdl1,port_hdl2,pps):
    log.info(banner("------SpirentHostBidirStream-----"))

    #op = uut.execute('show vrf all | incl vxlan')
    op = uut.execute('show nve vni  | incl L3')
    op1 = op.splitlines()
    vrf_list=[]
    for line in op1:
        if line:
            if 'own' in line:
                return 0
            else:
                vrf = line.split()[-1].replace("[","").replace("]","")
                vrf_list.append(vrf)

    for vrf in vrf_list:
        op = uut.execute('show ip int brief vrf {vrf}'.format(vrf=vrf))
        op1 = op.splitlines()
        vlan_list = []
        ip_list = []
        for line in op1:
            if line:
                if 'Vlan' in line:
                    if not 'forward-enabled' in line:
                        vlan_list.append(line.split()[0].replace("Vlan",""))
                        ip_list.append(line.split()[1])

        if not len(vlan_list) == len(ip_list):
            return 0
        else:
            gw1 = str(ip_address(ip_list[0]))
            ip1 = str(ip_address(gw1)+1)
            ip11= str(ip_address(ip1)+100)

            SpirentHostBidirStreamSmacSame(port_hdl1,port_hdl2,vlan_list[0],vlan_list[0],ip1,ip11,ip11,ip1,str(pps))

            for i in range(1,len(vlan_list)):
                vlan2 = vlan_list[i]
                gw2 = ip_list[i]
                ip2 = str(ip_address(gw2)+100)
                SpirentHostBidirStreamSmacSame(port_hdl1,port_hdl2,vlan_list[0],vlan2,ip1,ip2,gw1,gw2,str(pps))

    return 1



def SpirentHostBidirStreamSmacSame(port_hdl1,port_hdl2,vlan1,vlan2,ip1,ip2,gw1,gw2,rate_pps):
    log.info(banner("------SpirentHostBidirStream-----"))


    str11 = hex(int(vlan1))[2:][:2]
    str12 = hex(int(vlan1))[2:][1:]
    str21 = hex(int(vlan2))[2:][:2]
    str22 = hex(int(vlan2))[2:][1:]

    if vlan1==vlan2:
        mac1='00:10:'+str11+':'+str12+':'+str11+':22'
        mac2='00:11:'+str22+':'+str22+':'+str21+':44'
    else:
        mac1='00:10:'+str11+':'+str12+':'+str11+':22'
        mac2='00:10:'+str21+':'+str22+':'+str21+':22'


    log.info('IP1 : %r,IP2 : %r GW1 :%r GW2 :%r' ,ip1,ip2,gw1,gw2)
    device_ret1 =sth.emulation_device_config (mode = 'create', ip_version = 'ipv4',\
    encapsulation = 'ethernet_ii_vlan',vlan_id  = vlan1,port_handle = port_hdl1,\
    resolve_gateway_mac = 'true',intf_ip_addr= ip1,intf_prefix_len = '16',\
    gateway_ip_addr = gw1,mac_addr= mac1);

    device_ret2 =sth.emulation_device_config (mode = 'create', ip_version = 'ipv4',\
    encapsulation = 'ethernet_ii_vlan',vlan_id  = vlan2,port_handle = port_hdl2,\
    resolve_gateway_mac = 'true',intf_ip_addr= ip2,intf_prefix_len = '16',\
    gateway_ip_addr = gw2,mac_addr= mac2);

    h1 = device_ret1['handle']
    h2 = device_ret2['handle']

    streamblock_ret1 = sth.traffic_config (mode= 'create',port_handle= port_hdl1,\
    emulation_src_handle=h1,emulation_dst_handle = h2,bidirectional='1',\
    port_handle2=port_hdl2,transmit_mode='continuous',rate_pps=rate_pps)

    status = streamblock_ret1['status']

    log.info('+-----------------------------------------------------------------------+')
    log.info('stream_id : %r, vlan1 : %r ,vlan2 : %r ,rate_pps : %r',streamblock_ret1['stream_id'],vlan1,vlan2,rate_pps)
    log.info('IP1 : %r,IP2 : %r, Host1 : %r ,Host2 : %r ',ip1,ip2,h1,h2)
    log.info('+-----------------------------------------------------------------------+')
    if (status == '0') :
        log.info('run sth.traffic_config failed for V4 %r', streamblock_ret1)







def TriggerPortFlap(uut,port,count):
    for i in range(1,count):
        log.info("Shutting down Port %r",port)
        cfg = \
        """
        interface {port}
        shut
        """
        try:
            uut.configure(cfg.format(port=port))
        except:
            log.error(("Xconnect Orphan Port shut no shut Failed for port %r uut is %r",port,uut))
            return 0

        time.sleep(1)
        log.info("Un shutting down Port %r",port)
        cfg = \
        """
        interface {port}
        no shut
        """
        #log.info("cfg isssss %r",cfg.format(port=port))
        try:
            uut.configure(cfg.format(port=port))
        except:
            log.error(("Xconnect Orphan Port shut no shut Failed for port%r uut is %r",port,uut))
            return 0
    return 1





def VxlanStReset(uut_list):
    log.info(banner("Deleteing adding vxlan features"))
    cfg_shut =  \
    """
    interface {intf}
    shut
    """
    cfg_no_shut =  \
    """
    interface {intf}
    no shut
    """
    for uut in uut_list:
        op = uut.execute('show port-channel summary | incl Eth')
        op1 = op.splitlines()
        po_list = []
        for line in op1:
            if line:
                if not 'Po1(SU)' in line:
                    po = line.split()[1].split('(')[0]
                    po_list.append(po)
        for intf in po_list+["nve1"]:
            uut.configure(cfg_shut.format(intf=intf))

    countdown(60)

    for uut in uut_list:
        op = uut.execute('show port-channel summary | incl Eth')
        op1 = op.splitlines()
        po_list = []
        for line in op1:
            if line:
                if not 'Po1(SU)' in line:
                    po = line.split()[1].split('(')[0]
                    po_list.append(po)
        for intf in po_list+["nve1"]:
            uut.configure(cfg_no_shut.format(intf=intf))


    TriggerCoreIfFlap222(uut_list)

    countdown(200)

    for uut in uut_list:
        for feature in ['ospf','pim','bgp']:
            test1 = leaf_protocol_check222(uut,[feature])
            if not test1:
                log.info('Feature %r neigborship on device %r Failed ',feature,str(uut))
                return 0

    log.info(banner("Passed VxlanStReset"))
    return 1


def vPCMemberFlap(uut_list,po_list):
    log.info(banner("Starting TriggerCoreIfFlapStaticPo "))
    for uut in uut_list:
        for po in po_list:
            cmd = uut.execute("show interface po {po} | json-pretty ".format(po=po))
            op=json.loads(cmd)
            op1=op["TABLE_interface"]["ROW_interface"]["eth_members"]
            intf_list = []
            if len(op1.split()) > 1:
                for mem in op1.split():
                    if mem:
                        mem1 = mem.strip(",""")
                        intf_list.append(mem1)
            else:
                intf_list.append(op1)


        cfg = \
            """
            interface {intf}
            shut
            sleep 1
            no sh
            """

        for intf in intf_list:
            for i in range(1,3):
                try:
                    uut.configure(cfg.format(intf=intf))
                except:
                    log.info('Trigger4CoreIfFlapStaticPo failed @ 11')
                    return 0
    return 1



def TriggerCoreIfFlap222(uut_list):
    log.info(banner("Starting TriggerCoreIfFlapStaticPo "))
    for uut in uut_list:
        cmd = uut.execute("show ip ospf neigh | json-pretty")
        op=json.loads(cmd)
        op11 = op["TABLE_ctx"]['ROW_ctx']
        if 'list' in str(type(op11)):
            op1 = op11[0]["TABLE_nbr"]['ROW_nbr']
            nbrcount = op11[0]['nbrcount']
            core_intf_list = []
            if int(nbrcount) == 1:
                intf = op1[0]["intf"]
                core_intf_list.append(intf)
            else:
                for i in range(0,len(op1)):
                    intf = op1[i]["intf"]
                    core_intf_list.append(intf)

        else:
            op1 = op["TABLE_ctx"]['ROW_ctx']["TABLE_nbr"]['ROW_nbr']
            nbrcount = op["TABLE_ctx"]['ROW_ctx']['nbrcount']
            core_intf_list = []

            if int(nbrcount) == 1:
                intf = op1["intf"]
                core_intf_list.append(intf)
            else:
                for i in range(0,len(op1)):
                    intf = op1[i]["intf"]
                    core_intf_list.append(intf)

        for i in range(1,4):
            for intf in core_intf_list:
                cfg = \
                """
                interface {intf}
                shut
                """
                try:
                    uut.configure(cfg.format(intf=intf))
                except:
                    log.info('Trigger4CoreIfFlapStaticPo failed @ 11')
                    return 0

            countdown(1)
            for intf in core_intf_list:
                cfg = \
                """
                interface {intf}
                no shut
                """
                try:
                    uut.configure(cfg.format(intf=intf))
                except:
                    log.info('Trigger4CoreIfFlapStaticPo failed @ 11')
                    return 0

    return 1


def countdown(t):
    '''https://stackoverflow.com/questions/25189554/countdown-clock-0105'''
    while t:
        mins, secs = divmod(t, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        print(timeformat, end='\r')
        time.sleep(1)
        t -= 1


class VPCPoConfig(object):
    def __init__(self,node,vpc_po,vpc_po_mem_list1,vlan_range,vpc_po_type):
        self.node=node
        self.vpc_po=vpc_po
        self.vpc_po_mem_list1=vpc_po_mem_list1
        self.vlan_range=vlan_range
        self.vpc_po_type=vpc_po_type

    def vpc_conf(self):
        if 'access' in self.vpc_po_type:
            cmd = \
                '''
                vlan {vlan_range}
                interface port-channe {vpc_po}
                switchport
                switchport mode access
                switchport access vlan {vlan_range}
                no shut
                vpc {vpc_po}
                '''
            try:
                self.node.configure(cmd.format(vlan_range=self.vlan_range,vpc_po=self.vpc_po))
            except:
                log.error('444 vpc conf failed for vlan_range',self.vlan_range)


        elif 'trunk' in self.vpc_po_type:
            cmd = \
                '''
                vlan {vlan_range}
                interface port-channe {vpc_po}
                switchport
                switchport mode trunk
                switchport trunk allowed vlan {vlan_range}
                no shut
                vpc {vpc_po}
                '''
            try:
                self.node.configure(cmd.format(vlan_range=self.vlan_range,vpc_po=self.vpc_po))
            except:
                log.error('444 vpc conf failed for vlan_range',self.vlan_range)

        for intf in self.vpc_po_mem_list1:
            cmd = \
            '''
            interface {intf}
            channel-group {vpc_po} force mode active
            no shut
            '''
            try:
                self.node.configure(cmd.format(intf=intf,vpc_po=self.vpc_po))
            except:
                self.node.execute("show port-channel compatibility-parameters")
                log.error('555 vpc_po_mem conf failed for interface',intf)


           #time.sleep(30)
    def vpc_check(self):
        for node in [self.node]:
            filter1 = "Po"+str(self.vpc_po)
            print("VPC Po is .............",filter1)
            check1 = self.node.execute("show vpc | incl {filter1}".format(filter1=filter1))
            if "down" in check1:
                log.error('VPC Bringup failed for node',node)
                node.execute("show vpc consistency-parameters global")
                node.execute("show vpc consistency-parameters vpc {vpc_po}".format(vpc_po=self.vpc_po))
                self.failed


def find_svi_ip222(uut,svi):
    cmd = uut.execute("show int vlan {vlan} | json-pretty".format(vlan=svi))
    if not "svi_ip_addr" in str(cmd):
        log.info('svi_ip_addr found,Test failed')
        return 0

    else:
        test1=json.loads(cmd)
        test11 = test1["TABLE_interface"]["ROW_interface"]
        if 'list' in str(type(test11)):
            ip = test1["TABLE_interface"]["ROW_interface"][0]["svi_ip_addr"]
        else:
            ip = test1["TABLE_interface"]["ROW_interface"]["svi_ip_addr"]
        return ip



def findIntfIpv6Addr(uut,interface):
    '''
    cmd = uut.execute("show ipv6 interface {interface} | json-pretty".format(interface=interface))
    if not "addr" in str(cmd):
        log.info('svi_ip_addr found,Test failed')
        return 0

    else:
        test1=json.loads(cmd)
        #test11 = test1["TABLE_intf"]["ROW_intf"]

        if "version 9" in uut.execute('show ver'):
            #if test1["TABLE_intf"]["ROW_intf"]["addr"]:
            ip6 = test1["TABLE_intf"]["ROW_intf"]["addr"]

        elif "version 6" in uut.execute('show ver'):
            ip6 = test1["TABLE_intf"]["ROW_intf"]["TABLE_addr"]["ROW_addr"]["addr"]

        elif "version 7" in uut.execute('show ver'):
            ip6 = test1["TABLE_intf"]["ROW_intf"]["TABLE_addr"]["ROW_addr"]["addr"]

        ip6 = sub("/(.*)",'',ip6)

    return ip6
    '''
    cmd = uut.execute("show running-config interface {interface}".format(interface=interface))


    #def findIntfIpv6Addr(cmd):
    op=cmd.splitlines()
    for line in op:
        if 'ipv6 address' in line:
            ipv6_add = line.split()[-1]
            ip6 = sub("/(.*)",'',ipv6_add)
    return ip6


def VxanTcamCheckCarve(uut):
    """ function to configure interface default Global """
    log.info(banner("Entering proc configure interface default "))

    cfg_n9k = \
            """
            hardware access-list tcam region ifacl 0
            hardware access-list tcam region ipv6-ifacl 0
            hardware access-list tcam region mac-ifacl 0
            hardware access-list tcam region qos 0
            hardware access-list tcam region ipv6-qos 0
            hardware access-list tcam region mac-qos 0
            hardware access-list tcam region fex-ifacl 0
            hardware access-list tcam region fex-ipv6-ifacl 0
            hardware access-list tcam region fex-mac-ifacl 0
            hardware access-list tcam region fex-qos 0
            hardware access-list tcam region fex-ipv6-qos 0
            hardware access-list tcam region fex-mac-qos 0
            hardware access-list tcam region vacl 0
            hardware access-list tcam region ipv6-vacl 0
            hardware access-list tcam region mac-vacl 0
            hardware access-list tcam region vqos 0
            hardware access-list tcam region ipv6-vqos 0
            hardware access-list tcam region mac-vqos 0
            hardware access-list tcam region racl 1536
            hardware access-list tcam region ipv6-racl 0
            hardware access-list tcam region qos-lite 0
            hardware access-list tcam region fex-qos-lite 0
            hardware access-list tcam region vqos-lite 0
            hardware access-list tcam region l3qos-lite 0
            hardware access-list tcam region e-qos 0
            hardware access-list tcam region e-ipv6-qos 0
            hardware access-list tcam region e-mac-qos 0
            hardware access-list tcam region e-racl 768
            hardware access-list tcam region e-ipv6-racl 0
            hardware access-list tcam region e-qos-lite 0
            hardware access-list tcam region l3qos 256
            hardware access-list tcam region ipv6-l3qos 0
            hardware access-list tcam region mac-l3qos 0
            hardware access-list tcam region span 256
            hardware access-list tcam region copp 256
            hardware access-list tcam region svi 0
            hardware access-list tcam region redirect 256
            hardware access-list tcam region vpc-convergence 512
            hardware access-list tcam region ipsg 0
            hardware access-list tcam region rp-qos-lite 0
            hardware access-list tcam region rp-qos 256
            hardware access-list tcam region rp-ipv6-qos 256
            hardware access-list tcam region rp-mac-qos 256
            hardware access-list tcam region nat 0
            hardware access-list tcam region mpls 0
            hardware access-list tcam region n3k-qos-ipv4 0
            hardware access-list tcam region n3k-qos-ipv6 0
            hardware access-list tcam region sflow 0
            hardware access-list tcam region mcast_bidir 0
            hardware access-list tcam region openflow 0
            hardware access-list tcam region racl-udf 0
            hardware access-list tcam region racl-lite 0
            hardware access-list tcam region qos-intra-lite 0
            hardware access-list tcam region l3qos-intra-lite 0
            hardware access-list tcam region ifacl-udf 0
            hardware access-list tcam region copp-system 0
            hardware access-list tcam region ifacl-lite 0
            hardware access-list tcam region vacl-lite 0
            hardware access-list tcam region vqos-intra-lite 0
            hardware access-list tcam region ing-ifacl 0
            hardware access-list tcam region vacl 0
            hardware access-list tcam region ing-racl 0
            hardware access-list tcam region ing-rbacl 0
            hardware access-list tcam region ing-l2-qos 0
            hardware access-list tcam region ing-l3-vlan-qos 0
            hardware access-list tcam region ing-sup 0
            hardware access-list tcam region ing-l2-span-filter 0
            hardware access-list tcam region ing-l3-span-filter 0
            hardware access-list tcam region ing-fstat 0
            hardware access-list tcam region span 0
            hardware access-list tcam region egr-racl 0
            hardware access-list tcam region egr-sup 0
            hardware access-list tcam region openflow-lite 0
            hardware access-list tcam region fcoe-ingress 0
            hardware access-list tcam region fcoe-egress 0
            hardware access-list tcam region ing-redirect 0
            hardware access-list tcam region redirect-tunnel 0
            hardware access-list tcam region span-sflow 0
            hardware access-list tcam region openflow-ipv6 0
            hardware access-list tcam region mcast-performance 0
            hardware access-list tcam region egr-l2-qos 0
            hardware access-list tcam region egr-l3-vlan-qos 0
            hardware access-list tcam region n9k-arp-acl 0
            hardware access-list tcam region ipv6-span-udf 0
            hardware access-list tcam region ipv6-span-l2-udf 0
            hardware access-list tcam region ing-netflow 0
            hardware access-list tcam region ing-nbm 0
            hardware access-list tcam region redirect_v4 0
            hardware access-list tcam region redirect_v6 0
            hardware access-list tcam region tcp-nat 0
            hardware access-list tcam region vxlan-p2p 0
            hardware access-list tcam region arp-ether 256 double-wide
            """
    cfg_th = """
         hardware access-list tcam region arp-ether 256
         hardware access-list tcam region copp 256
         hardware access-list tcam region e-ipv6-qos 0
         hardware access-list tcam region e-ipv6-racl 0
         hardware access-list tcam region e-mac-qos 0
         hardware access-list tcam region e-qos 0
         hardware access-list tcam region e-qos-lite 0
         hardware access-list tcam region e-racl 0
         hardware access-list tcam region flow 0
         hardware access-list tcam region ifacl 0
         hardware access-list tcam region ipsg 0
         hardware access-list tcam region ipv6-ifacl 0
         hardware access-list tcam region ipv6-l3qos 0
         hardware access-list tcam region ipv6-qos 0
         hardware access-list tcam region ipv6-racl 0
         hardware access-list tcam region ipv6-vacl 0
         hardware access-list tcam region ipv6-vqos 0
         hardware access-list tcam region l3qos 0
         hardware access-list tcam region mac-ifacl 0
         hardware access-list tcam region mac-l3qos 0
         hardware access-list tcam region mac-qos 0
         hardware access-list tcam region mac-vacl 0
         hardware access-list tcam region mac-vqos 0
         hardware access-list tcam region mcast_bidir 0
         hardware access-list tcam region mpls 0
         hardware access-list tcam region openflow 0
         hardware access-list tcam region qos 0
         hardware access-list tcam region racl 256
         hardware access-list tcam region redirect 0
         hardware access-list tcam region redirect-tunnel 0
         hardware access-list tcam region span 0
         hardware access-list tcam region svi 0
         hardware access-list tcam region vacl 0
         hardware access-list tcam region vpc-convergence 0
         hardware access-list tcam region vqos 0
         hardware access-list tcam region nat 1536
         """

    cfg_n3k = """\
        hardware profile tcam region e-ipv6-qos 0
        hardware profile tcam region e-mac-qos 0
        hardware profile tcam region e-qos 0
        hardware profile tcam region e-qos-lite 0
        hardware profile tcam region e-racl 0
        hardware profile tcam region e-vacl 0
        hardware profile tcam region fhs 0
        hardware profile tcam region ifacl 0
        hardware profile tcam region ipv6-e-racl 0
        hardware profile tcam region ipv6-pbr 0
        hardware profile tcam region ipv6-qos 0
        hardware profile tcam region ipv6-racl 0
        hardware profile tcam region ipv6-span 0
        hardware profile tcam region ipv6-span-l2 0
        hardware profile tcam region mcast-bidir 0
        hardware profile tcam region qos 0
        hardware profile tcam region racl 256
        hardware profile tcam region vacl 0

        """


    mode = uut.execute("show system switch-mode")
    module = uut.execute("show module")
    if "not applicable for this platform" in mode:
        if not 'N3K-C30' in module:
            tcam=uut.execute("show hardware access-list tcam region | incl nat")
            tcam1 = tcam.splitlines()
            for line in tcam1:
                if "[nat]" in line:
                    nattcam =line.split()[-1]
                    if int(nattcam) < 1500:
                        if 'N3K-C32' in module:
                            uut.configure(cfg_th)
                        else:
                            uut.configure(cfg_n9k)
                        uut.execute('copy running-config startup-config')
                        log.info(banner("Reloading of devices"))
                        results1 = uut.reload()
                        if results1 != 0:
                            log.info(banner("uut Reload Passed"))
                        else:
                            log.info(banner("uut Reload Failed"))

    elif 'n3k' in mode:
        tcam=uut.execute("show hardware profile tcam region | incl nat")
        tcam1 = tcam.splitlines()
        for line in tcam1:
            print("line TCAM issss",line)
            if "nat size" in line:
                nattcam =line.split()[-1]
                print("nat TCAM issss nattcam nattcam",nattcam)
                if int(nattcam) < 1500:
                    uut.configure(cfg_n3k)
                    uut.execute('copy running-config startup-config')
                    log.info(banner("Reloading of devices"))
                    results1 = uut.reload()
                    if results1 != 0:
                        log.info(banner("uut Reload Passed"))
                    else:
                        log.info(banner("uut Reload Failed"))






def ProcessRestart(uut,proc):
    """ function to configure vpc """
    logger.info(banner("Entering proc to restart the processes"))
    try:
        config_str = '''sh system internal sysmgr service name {proc} | grep PID'''
        out=uut.execute(config_str.format(proc=proc))
        pid  = out.split()[5].strip(',')
        uut.transmit('run bash \r')
        uut.receive('bash-4.3$')
        uut.transmit('sudo su \r')
        uut.receive('bash-4.3$')
        uut.transmit('kill %s\r' %pid)
        uut.receive('bash-4.3$')
        uut.transmit('exit \r')
        uut.receive('bash-4.3$')
        uut.transmit('exit \r')
        uut.receive('#')

    except:
        log.error('proc restart test failed for %r',proc)
        log.error(sys.exc_info())





def NveChangeIrtoMcast(uut_list,mcast_group):
    log.info(banner("Starting NveMcastGroupChange "))

    for uut in uut_list:
        cmd = \
        """

        """
        op = uut.execute('show run interface nve 1')
        op1 = op.splitlines()
        for line in op1:
            cmd += line + '\n'
            if 'ingress-replication protocol bgp' in line:
                line = 'no ' +line
                cmd += line + '\n'
                line = '    mcast-group ' +str(mcast_group)
                cmd += line + '\n'
        log.info("cmd is %r",cmd)
        uut.configure(cmd)
    return 1




def NveChangeMcastToIr(uut_list):
    log.info(banner("Starting NveMcastGroupChange "))

    for uut in uut_list:
        cmd = \
        """

        """
        op = uut.execute('show run interface nve 1')
        op1 = op.splitlines()
        for line in op1:
            cmd += line + '\n'
            if 'mcast' in line:
                line = 'no ' +line
                cmd += line + '\n'
                line = 'ingress-replication protocol bgp'
                cmd += line + '\n'
        log.info("cmd is %r",cmd)
        uut.configure(cmd)
    return 1



def svi_remove(uut,vlan,vlan_scale):
    for j in range(0,vlan_scale):  # 5
            cmd += 'no interface Vlan{vlan}\n'.format(vlan=vlan)
            vlan = vlan + 1
    try:
        uut.configure(cmd)
    except:
        log.error('SVI configure failed for vlan')

def vrf_remove(uut,routed_vni,count):
    cmd=""
    for i in range(0,count):
        cmd +=  'no vrf context vxlan-{routed_vni}\n'.format(routed_vni=routed_vni)
        routed_vni = routed_vni + 1
    try:
        uut.configure(cmd)
    except:
        log.error('vrf configure failed for')



class LeafObjectFnL(object):
    def __init__(self,node,vlan,vni,vlan_scale,mcast_group,ir_mode,mcast_group_scale,peer_list):
        self.node=node
        self.vlan=vlan
        self.peer_list=peer_list
        self.vni=vni
        self.vlan_scale=vlan_scale
        self.mcast_group=mcast_group
        self.ir_mode=ir_mode
        self.mcast_group_scale=mcast_group_scale

        #ir_mode = bgp,mcast,mix

    def vxlan_conf(self):
        vlan_vni_configure(self.node,self.vlan,self.vni,self.vlan_scale)
        if 'mix' in self.ir_mode:
            log.info(banner("Replication mode is Static + MCAST"))
            #nve_configure_fl_mix(uut,vni,scale,peer_list,mcast_group,mcast_group_scale):
            nve_configure_fl_mix(self.node,self.vni,self.vlan_scale,self.peer_list,self.mcast_group,self.mcast_group_scale)
            #nve_configure_fl_mcast(self.node,self.vni,self.vlan_scale,self.mcast_group,self.mcast_group_scale)
        elif 'static' in self.ir_mode:
            log.info(banner("Replication mode is Static + MCAST"))
            nve_configure_fl_static(self.node,self.vni,self.vlan_scale,self.peer_list)
        elif 'mcast' in self.ir_mode:
            log.info(banner("Replication mode is Static + MCAST"))
            nve_configure_fl_mcast(self.node,self.vni,self.vlan_scale,self.mcast_group,self.mcast_group_scale)




def nve_configure_fl_mix(uut,vni,scale,peer_list,mcast_group,mcast_group_scale):
    vni1 = vni
    static_count=int(scale/2)
    vni2=vni1+static_count
    cmd1 = \
    """
    interface nve1
    no shutdown
    source-interface loopback0
    source-interface hold-down-time 20
    member vni {vni1}-{vni2}
    ingress-replication protocol static
    peer-ip {peer}
    """
    for peer in peer_list:
        uut.configure(cmd1.format(vni1=vni,vni2=vni2-1,peer=peer))

    a = mcast_group_scale # 4
    b = int(scale/2)  # 16
    c = int(b/a) # 4
    vnia = vni2
    vnib = vnia + c - 1

    for i in range(0,b,c):
        cmd = \
            """
            interface nve1
            no shutdown
            source-interface loopback0
            source-interface hold-down-time 20
            member vni {vnia}-{vnib}
            mcast-group {mcast_group}
            """
        uut.configure(cmd.format(vnia=vnia,vnib=vnib,mcast_group=mcast_group))
        vnia = vnia+c
        vnib = vnib+c
        mcast_group = ip_address(mcast_group) + 1


def nve_configure_fl_static(uut,static_vni,scale,peer_list):
    cmd1 = \
    """
    interface nve1
    no shutdown
    source-interface loopback0
    source-interface hold-down-time 20
    member vni {vni1}-{vni2}
    ingress-replication protocol static
    peer-ip {peer}
    """
    for peer in peer_list:
        uut.configure(cmd1.format(vni1=static_vni,vni2=static_vni+scale-1,peer=peer))


def nve_configure_fl_mcast(uut,mcast_vni,mcast_group,scale,mcast_group_scale):
    if mcast_group_scale == 1:
        cmd = \
        """
        interface nve1
        no shutdown
        source-interface loopback0
        source-interface hold-down-time 20
        member vni {vni1}-{vni2}
        mcast-group {mcast_group}
        """
        uut.configure(cmd.format(vni1=mcast_vni,vni2=mcast_vni+scale,mcast_group=mcast_group))


def AllTrafficTestL2(port_handle1,port_handle2,rate,pps,orphan_handle_list):
    rate3=int(rate)*3
    diff = int(rate3*.025)
    test1=SpirentRateTest22(port_handle1,port_handle2,rate3,diff)

    if not test1:
        log.info(banner("Rate test Failed"))
        return 0

    for port_hdl in orphan_handle_list:
        if port_hdl:
            res = sth.drv_stats(query_from = port_hdl,properties = "Port.TxTotalFrameRate Port.RxTotalFrameRate")
            rx_rate = res['item0']['PortRxTotalFrameRate']
            log.info('+----------------------------------------------------------------------+')
            log.info('+---- Acutual RX rate at Port %r is : %r ------+',port_hdl,rx_rate)
            log.info('+---- Expected RX rate at Port %r is : %r ------+',port_hdl,int(rate)*2)
            log.info('+----------------------------------------------------------------------+')
            if abs(int(rx_rate) - int(rate)*2) > diff:
                log.info('Traffic  Rate Test failed for %r',port_hdl)
                log.info('Stats are %r',res)
                return 0
    return 1



def NvePeerLearning2(port_handle_list,vlan,uut_list,peer_count,exclude_prefix):
    log.info(banner(" In NvePeerLearning"))

    for uut in uut_list:
        op1=uut.execute("sh nve peers  | grep nve1 | count")
        if not int(op1) == peer_count:
            log.info("Nve peer check failed for UUT %r",uut)
            uut.execute("sh nve peers")
            return 0

        aa=uut.execute("sh nve peers  | grep nve1")
        bb=aa.splitlines()
        for line in bb:
            if not exclude_prefix in line:
                if line:
                    if 'n/a' in line:
                       log.info(banner("RMAC NOT LEARNED"))
                       log.info("RMAC not learened @ uut %r",uut)
                       return 0

    log.info(banner("NvePeerLearning Passed"))
    return 1




def PortVlanMappingConfAll(uut_list,vlan_start,vlan_scale):
    log.info(banner("Starting PortVlanMapping "))

    for uut in uut_list:
        intf_list = []
        if 'vpc' in uut.execute("show run | incl feature"):
            op1 =  uut.execute("show vpc | json-pretty")
            op=json.loads(op1)
            intf=op["TABLE_vpc"]["ROW_vpc"]["vpc-ifindex"]
            intf_list.append(intf)
        op = uut.execute('show spanning-tree vlan {vlan_start} | incl FWD'.format(vlan_start=vlan_start))
        op1 = op.splitlines()
        for line in op1:
            if 'FWD' in line:
                if not 'peer-link' in line:
                    intf_list.append(line.split()[0])

        for intf in intf_list:
            cmd1 = \
            """
            interface {intf}
            switchport vlan mapping enable
            """
            vlan1 = vlan_start
            vlan2 = vlan1 + vlan_scale
            for i in range(1,vlan_scale+1):
                cmd1 +=  ' switchport vlan mapping {vlan2} {vlan1}\n'.format(vlan1=vlan1,vlan2=vlan2)
                vlan1 = vlan1 + 1
                vlan2 = vlan2 + 1
           #cmd1 +=  'switchport trunk allowed vlan {vlanA}-{vlan2}\n'.format(vlanA=vlan_start+vlan_scale,vlan2=vlan2)
            log.info("CMD ISSS -------------- %r",cmd1)
            try:
                uut.configure(cmd1.format(intf=intf))
            except:
                log.error('PVLAN Mapping failed for uut %r interface %r',uut,intf)
                return 0

    return 1





def PortVlanMappingRevertAll(uut_list,vlan_start,vlan_scale):
    log.info(banner("Starting PortVlanMapping "))
    vlan_end = vlan_start+vlan_scale
    for uut in uut_list:
        intf_list = []
        if 'vpc' in uut.execute("show run | incl feature"):
            op1 =  uut.execute("show vpc | json-pretty")
            op=json.loads(op1)
            intf=op["TABLE_vpc"]["ROW_vpc"]["vpc-ifindex"]
            intf_list.append(intf)
        op = uut.execute('show spanning-tree vlan {vlan_start} | incl FWD'.format(vlan_start=vlan_start))
        op1 = op.splitlines()
        for line in op1:
            if 'FWD' in line:
                if not 'peer-link' in line:
                    intf_list.append(line.split()[0])


        for intf in intf_list:
            cmd1 = \
            """
            interface {intf}
            shut
            """
            try:
                uut.configure(cmd1.format(intf=intf))
            except:
                log.error('PVLAN Mapping failed for uut %r interface %r',uut,intf)
                return 0

            countdown(5)

            cmd1 = \
            """
            interface {intf}
            """
            vlan1 = vlan_start
            vlan2 = vlan1 + vlan_scale
            for i in range(1,vlan_scale+1):
                cmd1 +=  ' no switchport vlan mapping {vlan2} {vlan1}\n'.format(vlan1=vlan1,vlan2=vlan2)
                vlan1 = vlan1 + 1
                vlan2 = vlan2 + 1
            cmd1 +=  'no switchport vlan mapping enable'
            log.info("CMD ISSS -------------- %r",cmd1)
            try:
                uut.configure(cmd1.format(intf=intf))
            except:
                log.error('PVLAN Mapping failed for uut %r interface %r',uut,intf)
                return 0

            cmd4 = \
            """
            interface {intf}
            switchport
            switchport mode trunk
            switchport trunk allowed vlan {vlan_start}-{vlan_end}
            spanning-tree bpdufilter enable
            spanning-tree port type edge trunk
            no shut
            """
            try:
                uut.configure(cmd4.format(intf=intf,vlan_start=vlan_start,vlan_end=vlan_end))
            except:
                log.error('PVLAN Mapping Remove failed for uut %r interface %r',uut,intf)
                return 0

    return 1





def SpirentRoutedBidirStreamPvlan(uut,port_hdl1,port_hdl2,pps,vlan_vni_scale):
    log.info(banner("------SpirentHostBidirStream-----"))

    op = uut.execute('show vrf all | incl vxlan')
    op1 = op.splitlines()
    vrf_list=[]
    for line in op1:
        if line:
            if 'own' in line:
                return 0
            else:
                vrf = line.split()[0]
                vrf_list.append(vrf)

    for vrf in vrf_list:
        op = uut.execute('show ip int brief vrf {vrf}'.format(vrf=vrf))
        op1 = op.splitlines()
        vlan_list = []
        ip_list = []
        for line in op1:
            if line:
                if 'Vlan' in line:
                    if not 'forward-enabled' in line:
                        vlan_list.append(int(line.split()[0].replace("Vlan",""))+vlan_vni_scale)
                        ip_list.append(line.split()[1])

        if not len(vlan_list) == len(ip_list):
            return 0
        else:
            gw1 = str(ip_address(ip_list[0]))
            ip1 = str(ip_address(gw1)+1)
            ip11= str(ip_address(ip1)+100)

            SpirentHostBidirStreamSmacSame(port_hdl1,port_hdl2,vlan_list[0],vlan_list[0],ip1,ip11,ip11,ip1,str(pps))

            for i in range(1,len(vlan_list)):
                vlan2 = vlan_list[i]
                gw2 = ip_list[i]
                ip2 = str(ip_address(gw2)+100)
                SpirentHostBidirStreamSmacSame(port_hdl1,port_hdl2,vlan_list[0],vlan2,ip1,ip2,gw1,gw2,str(pps))

    return 1



def NveL3VniRemoveAdd(uut_list):
    log.info(banner("Starting NveMcastGroupChange "))

    for uut in uut_list:
        cmd = \
        """
        interface nve1
        """
        op = uut.execute('show run int nve 1 | incl nve1|vrf')
        op1 = op.splitlines()
        for line in op1:
            if ' associate-vrf' in line:
                line = 'no ' + line
            cmd += line + '\n'
        log.info("removing L3 VNI  ")
        uut.configure(cmd)
        countdown(2)
        log.info("Adding  L3 VNI  ")
        uut.configure(op)

    return 1



def NveMcastGroupChange(uut_list):
    log.info(banner("Starting NveMcastGroupChange "))

    for uut in uut_list:
        cmd = \
        """

        """
        op = uut.execute('show run interface nve 1')
        op1 = op.splitlines()
        for line in op1:
            if 'mcast' in line:
                l = line.split()
                ip = ip_address(l[1])+10
                line = '    mcast-group ' +str(ip)
            cmd += line + '\n'

        #log.info("cmd is %r",cmd)
        uut.configure(cmd)
    return 1


def VnSegmentRemoveAdd(uut_list,vlan_start):
    log.info(banner("Starting NveMcastGroupChange "))

    for uut in uut_list:
        cmd = "show run vlan | begin 'vlan {vlan_start}'"

        vlan_run = uut.execute(cmd.format(vlan_start=vlan_start))

        cmd = " "

        #op = uut.execute('show run int nve 1 | incl nve1|vrf')
        op1 = vlan_run.splitlines()
        for line in op1:
            if 'vn-segment' in line:
                line = 'no ' + line
                cmd += line + '\n'
            else:
                cmd += line + '\n'


        cmd += 'exit' + '\n'
        try:
            log.info("removing vn-segment ")
            uut.configure(cmd)
            countdown(2)
            log.info("vn-segment  ")
            uut.configure(vlan_run)
        except:
            log.error('remove /add  vn-segment failed , uut is %r',uut)
            return 0

    return 1


def ChangeIRtoMcast(uut_list,mode,scale,mcast_group_scale,group_start):

    #for uut in uut_list:
    #    uut.configure(['interface nve1','shutdown'])
    #countdown(5)
    #vlan_vni_scale = 128
    #routing_vlan_scale = 8
    #mcast_group_scale = 8
    #ir_mode = 'mix'


    group= ip_address(group_start)+mcast_group_scale+1


    if 'mix' in mode:
        ir_scale = int(scale/2)
        vni_per_group = int(ir_scale/mcast_group_scale)
        for uut in uut_list:
            for vni in range(201001,201001+vni_per_group):
                uut.configure(['interface nve1',' member vni {vni}'.format(vni=vni),\
                'no ingress-replication protocol bgp',' mcast-group {group}'.format(group=group)])

    elif 'bgp' in mode:
        ir_scale = scale
        vni_per_group = int(ir_scale/mcast_group_scale)
        for uut in uut_list:
            for vni in range(201001,201001+vni_per_group):
                uut.configure(['interface nve1',' member vni {vni}'.format(vni=vni),\
                'no ingress-replication protocol bgp',' mcast-group {group}'.format(group=group)])


    countdown(5)
    ##for uut in uut_list:
    #    uut.configure(['interface nve1', 'no shutdown'])
    #countdown(5)
    return 1


def FloodTrafficGeneratorScaleArp22(port_handle,vlan,ip_sa,ip_da,rate_pps,count,mac_src):
    #host_count = int(count)*100
    device_ret = sth.traffic_config (
        mode            =       'create',
        port_handle     =       port_handle,
        l2_encap        =       'ethernet_ii_vlan',
        vlan_id         =       vlan,
        vlan_id_count   =       count,
        vlan_id_mode    =       'increment',
        l3_protocol     =       'ipv4',
        ip_src_addr     =       ip_sa,
        ip_src_step     =       '0.1.0.0',
        ip_src_count    =       count,
        ip_src_mode     =       'increment',
        ip_dst_addr     =       ip_da,
        mac_dst         =       'ff:ff:ff:ff:ff:ff',
        mac_src         =       mac_src,
        mac_src_count   =       arp_count,
        mac_src_mode    =       'increment',
        rate_pps        =       rate_pps,
        transmit_mode   =       'continuous')

    status = device_ret['status']
    if (status == '0') :
        log.info("run sth.emulation_device_config failed")
        return 0
    else:
        log.info("***** run sth.emulation_device_config successfully")
        return 1


def arp_supp_add_final(uut):

    op = uut.execute('show run int nve1 | beg nve1')
    op1 = op.splitlines()
    cmd = " "
    for line in op1:
        if line:
            cmd += line + '\n'
            if 'ingress-replication' in line:
                line1 = 'suppress-arp'
                cmd += line1 + '\n'
            elif 'mcast-group ' in line:
                line2 = 'suppress-arp'
                cmd += line2 + '\n'
    try:
        uut.configure(cmd)
    except:
        log.error('arp_supp_add_final failed ')
        #return 0





def CheckOspfUplinkRate(uut_list,pps):
    log.info(banner("Starting TriggerCoreIfFlapStaticPo "))
    for uut in uut_list:
        cmd = uut.execute("show ip ospf neigh | json-pretty")
        op=json.loads(cmd)
        #op11 = op["TABLE_ctx"]['ROW_ctx']
        op1 = op["TABLE_ctx"]['ROW_ctx']["TABLE_nbr"]['ROW_nbr']
        nbrcount = op["TABLE_ctx"]['ROW_ctx']['nbrcount']

        core_intf_list = []

        if int(nbrcount) == 1:
            intf = op1["intf"]
            if not 'lan' in intf:
                core_intf_list.append(intf)
        else:
            for i in range(0,len(op1)):
                intf = op1[i]["intf"]
                if not 'lan' in intf:
                    core_intf_list.append(intf)

        for intf in core_intf_list:
            cmd = uut.execute('show interface {intf} counters brief | json-pretty'.format(intf=intf))
            op=json.loads(cmd)
            rate= op['TABLE_interface']['ROW_interface']['eth_outrate1']
            if int(rate) > pps:
                return 0

    return 1



def SpirentArpRateTest(port_hdl_list1,port_hdl_list2,rate_fps,diff,arp_sa_state):
    log.info(banner(" Starting SpirentArpRateTest "))

    result = 1
    if 'on' in arp_sa_state:
        for port_hdl in port_hdl_list1:
            log.info("port_hdl %r,rate_fps %r", port_hdl,rate_fps)
            res = sth.drv_stats(query_from = port_hdl,properties = "Port.TxTotalFrameRate Port.RxTotalFrameRate")
            rx_rate = res['item0']['PortRxTotalFrameRate']
            tx_rate = res['item0']['PortTxTotalFrameRate']
            log.info('+-----------------------------------------------------------------------+')
            log.info('rx_rate is %r,tx_rate is %r',rx_rate,tx_rate)
            log.info('+-----------------------------------------------------------------------+')

            if abs(int(tx_rate) - int(rate_fps)) > diff:
                log.info('TX rate low with SA enabled, rate is %r',tx_rate)
                result = 0

            if int(rx_rate) > 5*int(diff):
                log.info('ARP Rate Test failed with SA enabled, rate is %r',rx_rate)
                result = 0

            if int(rx_rate) < int(diff):
                log.info('vTEP may not be sending out the Arp Response, rate is %r',rx_rate)
                result = 0


        for port_hdl in port_hdl_list2:
            log.info("port_hdl %r", port_hdl)
            res = sth.drv_stats(query_from = port_hdl,properties = "Port.TxTotalFrameRate Port.RxTotalFrameRate")
            rx_rate = res['item0']['PortRxTotalFrameRate']
            tx_rate = res['item0']['PortTxTotalFrameRate']
            log.info('+-----------------------------------------------------------------------+')
            log.info('rx_rate is %r,tx_rate is %r',rx_rate,tx_rate)
            log.info('+-----------------------------------------------------------------------+')

            if int(rx_rate) > 2*(int(diff)):
                log.info('ARP Rate Test failed with SA enabled, rate at orphan port is %r',rx_rate)
                result = 0


    elif 'off' in arp_sa_state:
        for port_hdl in port_hdl_list1:
            log.info("port_hdl %r,rate_fps %r", port_hdl,rate_fps)
            res = sth.drv_stats(query_from = port_hdl,properties = "Port.TxTotalFrameRate Port.RxTotalFrameRate")
            rx_rate = res['item0']['PortRxTotalFrameRate']
            tx_rate = res['item0']['PortTxTotalFrameRate']
            log.info('+-----------------------------------------------------------------------+')
            log.info('rx_rate is %r,tx_rate is %r',rx_rate,tx_rate)
            log.info('+-----------------------------------------------------------------------+')

            if abs(int(rx_rate) - int(tx_rate)) > 4*int(diff):
                log.info('Traffic  Rate Test failed - TX / RX difference is %r',abs(int(rx_rate) - int(tx_rate)))
                result = 0

            if abs(int(rx_rate) - int(rate_fps)) > 4*int(diff):
                log.info('Traffic  Rate Test failed, Rate & FPS diff is %r',abs(int(rx_rate) - int(rate_fps)))
                result = 0

        for port_hdl in port_hdl_list2:
            log.info("port_hdl %r", port_hdl)
            res = sth.drv_stats(query_from = port_hdl,properties = "Port.TxTotalFrameRate Port.RxTotalFrameRate")
            rx_rate = res['item0']['PortRxTotalFrameRate']
            tx_rate = res['item0']['PortTxTotalFrameRate']
            log.info('+-----------------------------------------------------------------------+')
            log.info('rx_rate is %r,tx_rate is %r',rx_rate,tx_rate)
            log.info('+-----------------------------------------------------------------------+')

            if abs(int(rx_rate) - 2*(int(rate_fps))) > 5*int(diff):
                log.info('ARP Rate Test failed with SA Disabled, rate at orphan port is %r',rx_rate)
                result = 0

    return result



def ArpSuppressTrafficGenerator(port_handle,vlan,ip_sa,ip_da,mac_sa,rate_pps,count):
    #log.info("port_handle %r vlan %r ip_sa %r ip_da %r mac_sa %r ",port_handle,vlan,ip_sa,ip_da,mac_sa)
    log.info(banner("------in ArpSuppressTrafficGenerator-----"))

    #for vlan in range(int(vlan),int(vlan)+int(count)):
    vlan = str(vlan)

    streamblock_ret1 = sth.traffic_config (
        mode = 'create',
        port_handle = port_handle,
        l2_encap = 'ethernet_ii_vlan',
        vlan_id=vlan,
        vlan_id_count=count,
        vlan_id_mode='increment',
        l3_protocol = 'arp',
        ip_src_addr = ip_sa,
        ip_src_count = count,
        ip_src_mode = 'increment',
        ip_src_step ='0.1.0.0',
        ip_dst_addr = ip_da,
        ip_dst_count = count,
        ip_dst_mode = 'increment',
        ip_dst_step ='0.1.0.0',
        arp_src_hw_addr = mac_sa,
        arp_src_hw_mode = 'increment',
        arp_src_hw_count = count,
        arp_dst_hw_addr = "00:00:00:00:00:00",
        arp_dst_hw_mode = "fixed",
        arp_operation = "arpRequest",
        rate_pps = rate_pps,
        mac_src = mac_sa,
        mac_dst = 'ff:ff:ff:ff:ff:ff',
        mac_src_count= count,
        mac_src_mode='increment',
        mac_src_step='00:00:00:00:00:01',
        transmit_mode = 'continuous')



def FloodTrafficGeneratorScaleArp(port_handle,vlan,ip_sa,ip_da,rate_pps,count,mac_src):
    #host_count = int(count)*100
    device_ret = sth.traffic_config (
        mode            =       'create',
        port_handle     =       port_handle,
        l2_encap        =       'ethernet_ii_vlan',
        vlan_id         =       vlan,
        vlan_id_count   =       count,
        vlan_id_mode    =       'increment',
        l3_protocol     =       'ipv4',
        ip_src_addr     =       ip_sa,
        ip_src_step     =       '0.1.0.0',
        ip_src_count    =       count,
        ip_src_mode     =       'increment',
        ip_dst_addr     =       ip_da,
        mac_dst         =       'ff:ff:ff:ff:ff:ff',
        mac_src         =       mac_src,
        mac_src_count   =       count,
        mac_src_mode    =       'increment',
        rate_pps        =       rate_pps,
        transmit_mode   =       'continuous')

    status = device_ret['status']
    if (status == '0') :
        log.info("run sth.emulation_device_config failed")
        return 0
    else:
        log.info("***** run sth.emulation_device_config successfully")
        return 1


def arp_supp_remove_final(uut):

    op = uut.execute('show run int nve1 | beg nve1')
    op1 = op.splitlines()
    cmd = " "
    for line in op1:
        if line:
            if 'suppress-arp' in line:
                line = 'no suppress-arp'
        cmd += line + '\n'
    try:
        uut.configure(cmd)
    except:
        log.error('arp_supp_remove_final failed ')
        #return 0


def pingtest(uut,dest_ip):
    log.info("----------sw1.send(ping %r count unlimited timeout 0) -------------",dest_ip)
    try:
        uut.execute("ping {dest_ip} count 10000 timeout 0".format(dest_ip=dest_ip))
    except:
        log.error('ping failed')
        return 0
    return 1

def captest(uut):
    cmd1 = "ethanalyzer local interface inband detail | incl 'CFI: 0, ID: 1001'"
    cap1 = uut.execute(cmd1)
    #if '1001' in cap1:
    #    log.info('capture is %r',cap1)
    return str(cap1)
    #return 1


def SpirentRoutedBidirStreamInspur(port_hdl1,port_hdl2,vlan1,vlan2,ip1,ip2,gw1,gw2,rate_pps):
    log.info(banner("------SpirentRoutedBidirStreamInspur-----"))

    if 'Nil' in vlan1 and 'Nil' in vlan2:
        str11 = hex(int(1001))[2:][:2]
        str12 = hex(int(1001))[2:][1:]
        str21 = hex(int(1002))[2:][:2]
        str22 = hex(int(1002))[2:][1:]

        mac1='00:10:'+str11+':'+str12+':'+str11+':22'
        mac2='00:11:'+str22+':'+str22+':'+str21+':44'


        log.info('IP1 : %r,IP2 : %r GW1 :%r GW2 :%r' ,ip1,ip2,gw1,gw2)
        device_ret1 =sth.emulation_device_config (mode = 'create', ip_version = 'ipv4',\
        encapsulation = 'ethernet_ii',port_handle = port_hdl1,\
        resolve_gateway_mac = 'true',intf_ip_addr= ip1,intf_prefix_len = '16',\
        gateway_ip_addr = gw1,mac_addr= mac1);

        device_ret2 =sth.emulation_device_config (mode = 'create', ip_version = 'ipv4',\
        encapsulation = 'ethernet_ii',port_handle = port_hdl2,\
        resolve_gateway_mac = 'true',intf_ip_addr= ip2,intf_prefix_len = '16',\
        gateway_ip_addr = gw2,mac_addr= mac2);

        h1 = device_ret1['handle']
        h2 = device_ret2['handle']

    elif not 'Nil' in vlan1 and 'Nil' in vlan2:
        str11 = hex(int(vlan1))[2:][:2]
        str12 = hex(int(vlan1))[2:][1:]
        str21 = hex(int(1001))[2:][:2]
        str22 = hex(int(1001))[2:][1:]

        mac1='00:10:'+str11+':'+str12+':'+str11+':22'
        mac2='00:11:'+str22+':'+str22+':'+str21+':44'

        log.info('IP1 : %r,IP2 : %r GW1 :%r GW2 :%r' ,ip1,ip2,gw1,gw2)
        device_ret1 =sth.emulation_device_config (mode = 'create', ip_version = 'ipv4',\
        encapsulation = 'ethernet_ii_vlan',vlan_id  = vlan1,port_handle = port_hdl1,\
        resolve_gateway_mac = 'true',intf_ip_addr= ip1,intf_prefix_len = '16',\
        gateway_ip_addr = gw1,mac_addr= mac1);


        device_ret2 =sth.emulation_device_config (mode = 'create', ip_version = 'ipv4',\
        encapsulation = 'ethernet_ii',port_handle = port_hdl2,\
        resolve_gateway_mac = 'true',intf_ip_addr= ip2,intf_prefix_len = '16',\
        gateway_ip_addr = gw2,mac_addr= mac2);

        h1 = device_ret1['handle']
        h2 = device_ret2['handle']

    elif not 'Nil' in vlan2 and 'Nil' in vlan1:
        str11 = hex(int(vlan2))[2:][:2]
        str12 = hex(int(vlan2))[2:][1:]
        str21 = hex(int(1001))[2:][:2]
        str22 = hex(int(1001))[2:][1:]

        mac1='00:10:'+str11+':'+str12+':'+str11+':22'
        mac2='00:11:'+str22+':'+str22+':'+str21+':44'

        log.info('IP1 : %r,IP2 : %r GW1 :%r GW2 :%r' ,ip1,ip2,gw1,gw2)
        device_ret1 =sth.emulation_device_config (mode = 'create', ip_version = 'ipv4',\
        encapsulation = 'ethernet_ii',port_handle = port_hdl1,\
        resolve_gateway_mac = 'true',intf_ip_addr= ip2,intf_prefix_len = '16',\
        gateway_ip_addr = gw2,mac_addr= mac2);

        device_ret2 =sth.emulation_device_config (mode = 'create', ip_version = 'ipv4',\
        encapsulation = 'ethernet_ii_vlan',vlan_id  = vlan2,port_handle = port_hdl2,\
        resolve_gateway_mac = 'true',intf_ip_addr= ip1,intf_prefix_len = '16',\
        gateway_ip_addr = gw1,mac_addr= mac1);


        h1 = device_ret1['handle']
        h2 = device_ret2['handle']


    streamblock_ret1 = sth.traffic_config (mode= 'create',port_handle= port_hdl1,\
    emulation_src_handle=h1,emulation_dst_handle = h2,bidirectional='1',\
    port_handle2=port_hdl2,transmit_mode='continuous',rate_pps=rate_pps)

    status = streamblock_ret1['status']

    log.info('+-----------------------------------------------------------------------+')
    log.info('stream_id : %r, vlan1 : %r ,vlan2 : %r ,rate_pps : %r',streamblock_ret1['stream_id'],vlan1,vlan2,rate_pps)
    log.info('IP1 : %r,IP2 : %r, Host1 : %r ,Host2 : %r ',ip1,ip2,h1,h2)
    log.info('+-----------------------------------------------------------------------+')
    if (status == '0') :
        log.info('run sth.traffic_config failed for V4 %r', streamblock_ret1)


def tgnHostCreate(port_hdl,ipv4_add,ipv4_gw,**kwargs):
    vlan = kwargs.get("vlan", None)
    mac_add = kwargs.get("mac_add", None)
    intf_prefix_len = kwargs.get("intf_prefix_len", None)

    if not intf_prefix_len:
        intf_prefix_len = '16'
    if not mac_add:
        mac_add1 = str(RandMac("00:00:00:00:00:00", True))
        mac_add = mac_add1.replace("'","")
    #try:
    if not vlan:
        device_ret =sth.emulation_device_config (mode = 'create', ip_version = 'ipv4',\
        encapsulation = 'ethernet_ii',port_handle = port_hdl,\
        resolve_gateway_mac = 'true',intf_ip_addr= ipv4_add,intf_prefix_len = intf_prefix_len,\
        gateway_ip_addr = ipv4_gw,mac_addr= mac_add);
    else:
        device_ret =sth.emulation_device_config (mode = 'create', ip_version = 'ipv4',\
        encapsulation = 'ethernet_ii_vlan',vlan_id  = vlan,port_handle = port_hdl,\
        resolve_gateway_mac = 'true',intf_ip_addr= ipv4_add,intf_prefix_len = intf_prefix_len,\
        gateway_ip_addr = ipv4_gw,mac_addr= mac_add);

    host = device_ret['handle']
    log.info('Created host is %r, returning host ',host)
    return host

def tgnBidirStreamCreate(port_hdl1,port_hdl2,host_src_handle,host_dst_handle,rate_pps):
    streamblock_ret1 = sth.traffic_config (mode= 'create',port_handle= port_hdl1,\
    emulation_src_handle=host_src_handle,emulation_dst_handle = host_dst_handle,bidirectional='1',\
    port_handle2=port_hdl2,transmit_mode='continuous',rate_pps=rate_pps)

    status = streamblock_ret1['status']


def CreateSpirentStreams2223(port_hdl,ip_src,ip_dst,mac_src,mac_dst,stream_id,rate_pps,smac_count,dmac_count,dmac_step,dmac_mode,smac_mode,transmit_mode,smac_step,vlan_id):
    #self,port_hdl_list,ip_src_list,ip_dst_list,mac_src_list,mac_dst_list,stream_list,rate_pps,mac_count,mac_mode,mac_step,vlan_id):
    """ function to configure Stream """
    logger.info(banner("Entering proc to configure streams in Spirent"))
    try:
        streamblock_ret1 = sth.traffic_config (
                mode = 'create',
                port_handle = port_hdl,
                l2_encap = 'ethernet_ii_vlan',
                frame_size_min='500',
                frame_size_max='9000',
                frame_size_step='500',
                vlan_id=vlan_id,
                l3_protocol = 'ipv4',
                ip_id = '0',
                ip_src_addr = ip_src,
                ip_dst_addr = ip_dst,
                ip_dst_count = '20',
                ip_dst_mode = 'increment',
                ip_dst_step ='0.0.0.1',
                ip_ttl = '255',
                ip_hdr_length = '5',
                ip_protocol = '253',
                mac_src = mac_src,
                mac_dst = mac_dst,
                mac_dst_count = dmac_count,
                mac_dst_mode = dmac_mode,
                mac_dst_step = dmac_step,
                mac_src_count= smac_count,
                mac_src_mode=smac_mode,
                mac_src_step=smac_step,
                stream_id = stream_id,
                rate_pps = rate_pps,
                fill_type = 'constant',
                fcs_error = '0',
                fill_value = '0',
                traffic_state = '1',
                length_mode = 'fixed',
                disable_signature = '0',
                enable_stream_only_gen= '1',
                pkts_per_burst = '1',
                inter_stream_gap_unit= 'bytes',
                burst_loop_count = '30',
                transmit_mode = transmit_mode,
                inter_stream_gap = '12',
                mac_discovery_gw = ip_dst)

        status = streamblock_ret1['status']

        if (status == '0') :
            log.info('run sth.traffic_config failed for V4 %r', streamblock_ret1)

    except:
        log.error('Spirect traffic config failed')
        log.error(sys.exc_info())



def clearConsole(ts,port_list):
    switch = pexpect.spawn('telnet {ts}'.format(ts=ts))
    switch.logfile = sys.stdout
    switch.expect("Username:")
    switch.sendline("lab")
    switch.expect("Password:")
    switch.sendline("lab")
    switch.expect("#")
    for line in port_list:
        for i in range(1,10):
            switch.sendline("clear line {line}".format(line=int(line)))
            switch.expect('[confirm]')
            switch.sendline("\r\n")
            switch.expect("#")


def ConfigureEsiGlobal(uut):
    """ function to configure ESI Global """
    logger.info(banner("Entering proc configure ESI Nodes"))

    config_str = \
        """
        no feature vpc
        evpn esi multihoming
        ethernet-segment delay-restore time 30
        vlan-consistency-check
        """
    try:
        uut.configure(config_str)
        log.info('ESI global config PASSED in uut %r',uut)
    except:
        log.info('ESI global config FAILED in uut %r',uut)
        return 0




def ConfigureEsiGlobal(uut):
    """ function to configure ESI Global """
    logger.info(banner("Entering proc configure ESI Nodes"))

    config_str = \
        """
        no feature vpc
        evpn esi multihoming
        ethernet-segment delay-restore time 30
        vlan-consistency-check
        """
    try:
        uut.configure(config_str)
        log.info('ESI global config PASSED in uut %r',uut)
    except:
        log.info('ESI global config FAILED in uut %r',uut)
        return 0



def ConfigureEsiPo(uut,esid,sys_mac,esi_po,vlan_range,mode,member_list):
    """ function to configure ESI Global """
    logger.info(banner("Entering proc configure ESI Po"))
    if 'access' in mode:
        config_str = \
        '''
        no interface port-channel {esi_po}
        interface port-channel {esi_po}
        #port-channel mode active
        no shut
        switchport
        switchport mode access
        no shut
        switchport access vlan {vlan_range}
        ethernet-segment {esid}
        system-mac {sys_mac}
        mtu 9216
        '''

    elif 'trunk' in mode:

        config_str = \
        """
        no interface port-channel {esi_po}
        interface port-channel {esi_po}
        #port-channel mode active
        no shut
        switchport
        switchport mode trunk
        no shut
        switchport trunk allowed vlan {vlan_range}
        ethernet-segment {esid}
        system-mac {sys_mac}
        mtu 9216
        """
    #try:
    uut.configure(config_str.format(esid=esid,sys_mac=sys_mac,esi_po=esi_po,vlan_range=vlan_range))
    log.info('ESI Po %r config PASSED in uut %r',esi_po,uut)
    #except:
    #log.info('ESI Po %r config FAILED in uut %r',esi_po,uut)
    #return 0

    for intf in member_list:
        config_str = \
        '''
        default interface {intf}
        interface {intf}
        channel-group {esi_po} force mode active
        no shut
        '''
        try:
            uut.configure(config_str.format(intf=intf,esi_po=esi_po))
        except:
            log.info('ESI Po %r member %r config FAILED in uut %r',esi_po,intf,uut)
            return 0

    return 1


class EsiNode(object):
    def __init__(self,node,esid,sys_mac,esi_po,esi_mem_list1,vlan_range,esi_po_type):
        self.node=node
        self.esid=esid
        self.sys_mac=sys_mac
        self.esi_po=esi_po
        self.esi_mem_list1=esi_mem_list1
        self.vlan_range=vlan_range
        self.esi_po_type=esi_po_type

    def esi_configure(self):
        result = ConfigureEsiPo(self.node,self.esid,self.sys_mac,self.esi_po,self.vlan_range,self.esi_po_type,self.esi_mem_list1)


class leaf(object):
    '''
    leaf1-
    loop - pri/sec
    access -  vpc/orp - acc/trunk
    uplink - po/ip/unnumb
    igp - ospf/isis / v6
    pim - rp
    bgp - as
    vxlan - mode
    bgw - type
    '''

    def __init__(self,node,vlan_range):
        self.node=node
        self.vlan_range=vlan_range

        log.info("leaf device is %r",self.node)
 

    def loopback_configure(self):
        for intf in self.node.interfaces.keys():
            if 'loopback' in intf:
                intf=self.node.interfaces[intf].intf
                log.info("loopback intf is %r  on leaf device  %r",intf,self.node)
                if 'ipv4_sec' in dir(self.node.interfaces[intf]):
                    ipv4_add_sec = self.node.interfaces[intf].ipv4_sec
                    ipv4_add=self.node.interfaces[intf].ipv4
                    log.info('ipv4_add is %r ipv4_add_sec is %r on leaf device %r',ipv4_add,ipv4_add_sec,self.node)
                    ConfigLoopback(self.node,intf,ipv4_add,ipv4_add_sec)

                else:
                    ipv4_add=self.node.interfaces[intf].ipv4
                    log.info('ipv4_add is %r on leaf device  %r ',ipv4_add,self.node)
                    ConfigLoopback(self.node,intf,ipv4_add,'Nil')

    def l3_port_configure(self):
        spine_leaf_intf_list = []
        log.info("+++++++++++++1111111++++++++++++++++++++++++++++++")
        log.info("uut.interfaces.keys() are %r",self.node.interfaces.keys())
        log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        for intf in self.node.interfaces.keys():
            if 'Eth' in self.node.interfaces[intf].intf:
                if 'leaf_spine' in self.node.interfaces[intf].alias:
                    intf=self.node.interfaces[intf].intf
                    log.info("leaf_spine intf is %r  on leaf device  %r",intf,self.node)
                    spine_leaf_intf_list.append(intf)

        log.info("spine_leaf_intf_list is %r  on leaf device  %r",spine_leaf_intf_list,self.node)

        log.info("+++++++++++222222222+++++++++++++++++++++++++")
        log.info("uut.interfaces.keys() are %r",self.node.interfaces.keys())
        log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++")



        for intf in spine_leaf_intf_list:
            eth = Interface(name=intf)
            eth.device = self.node
            eth.description = 'leaf_spine'
            eth.shutdown = False
            eth.mtu = 9216
            eth.medium = 'p2p'
            eth.unnumbered_intf_ref = 'loopback1'
            log.info("Configuring interface %r in device %r",intf,self.node)
            configuration = eth.build_config()


        log.info("+++++++++++333333333+++++++++++++++++++++++++")
        log.info("uut.interfaces.keys() are %r",self.node.interfaces.keys())
        log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++")



    def underlay_igp_configure(self):
        ipv4_add=self.node.interfaces['loopback1'].ipv4.ip
        ospf1 = Ospf()
        self.node=add_feature(ospf1)
        ospf1.device_attr[self.node].vrf_attr["default"].instance = '1'
        ospf1.device_attr[self.node].vrf_attr["default"].router_id = ipv4_add

        for intf in self.node.interfaces.keys():
            intf=self.node.interfaces[intf].intf
            if "oopback" in intf.name or "leaf" in intf.alias:
                ospf1.device_attr[self.node].vrf_attr["default"].area_attr['0'].interface_attr[intf].if_admin_control = True
        
        ospf1.build_config()


    def access_port_configure(self):
        vpc_access_port_member_list = []
        esi_access_port_member_list = []
        mct_port_member_list = []



        log.info("+++++++++++444444444+++++++++++++++++++++++++")
        log.info("uut.interfaces.keys() are %r",self.node.interfaces.keys())
        log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++")


        uut=self.node
        vlan_range = self.vlan_range
 
        log.info("+++++++++++55555555+++++++++++++++++++++++++")
        log.info("uut.interfaces.keys() are %r",self.node.interfaces.keys())
        log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++")


        log.info(banner("-----FAILURE--66666---"))      
        log.info("uut.interfaces.keys() are %r",uut.interfaces.keys())

        for intf in uut.interfaces.keys():
            log.info("Checking port %r on leaf device %r for tgn connection",intf,uut)
            if not 'Eth' in str(intf):
                if 'Eth' in uut.interfaces[intf].intf:
                    if 'tgn' in uut.interfaces[intf].alias:
                        log.info("Configuring port %r on leaf device %r for tgn connection",intf,uut)
                        intf=uut.interfaces[intf].intf
                        try:
                            AccesPortconfigs(uut,intf,vlan_range)
                        except:
                            log.error('AccesPortconfigs failed for port %r @ uut %r',intf,uut)
 
        for intf in uut.interfaces.keys():
            if 'mct_po' in uut.interfaces[intf].alias:
                log.info("mct port-channel is %r on leaf device  %r",intf,uut)
                mct_po_number = uut.interfaces[intf].intf
                src_ip = uut.interfaces[intf].src_ip
                peer_ip = uut.interfaces[intf].peer_ip

            elif 'vpc_po' in uut.interfaces[intf].alias:
                log.info("vpc port-channel is %r on leaf device  %r",intf,uut)
                vpc_po_number = uut.interfaces[intf].intf

        for intf in uut.interfaces.keys():            
            if 'Eth' in uut.interfaces[intf].intf:
                
                if 'esi_access' in uut.interfaces[intf].alias:
                    intf=uut.interfaces[intf].intf
                    log.info("adding esi port-channel member %r on leaf device  %r",intf,uut)
                    esi_access_port_member_list.append(intf)

                elif 'vpc_access' in uut.interfaces[intf].alias:
                    intf=uut.interfaces[intf].intf
                    log.info("adding vpc port-channel member %r on leaf device  %r",intf,uut)
                    vpc_access_port_member_list.append(intf)

                elif 'mct_link' in suut.interfaces[intf].alias:
                    intf=uut.interfaces[intf].intf
                    log.info("adding mct port-channel member %r on leaf device  %r",intf,uut)
                    mct_port_member_list.append(intf)

        for intf in uut.interfaces.keys():
            if 'vpc_po' in uut.interfaces[intf].alias:
                intf=uut.interfaces[intf].intf
                log.info("Configureing VPC port-channel  %r on leaf device  %r",intf,uut)
                try:
                    vtep_vpc_global_obj1 = VPCNodeGlobal(uut,mct_po_number,str(peer_ip),\
                    mct_port_member_list,str(src_ip))
                    vtep_vpc_global_obj1.vpc_global_conf()
                except:
                    log.error('vtep_vpc_global_obj1.vpc_global_conf failed')

                try:
                    vtep_vpc_obj1 = VPCPoConfig(uut,vpc_po_number,vpc_access_port_member_list,\
                    vlan_range,'trunk')
                    vtep_vpc_obj1.vpc_conf()
                except:
                    log.error('vtep_vpc_obj1.vpc_conf failed')





def leafGlobalConfig(uut):
    cmd=\
            '''
            fabric forwarding anycast-gateway-mac 0000.2222.3333
            '''
    try:
        uut.configure(cmd.format(rid=rid,pim_rp_address=pim_rp_address))
    except:
        log.error('OSPF config failed for node',uut)

def leafOspfConfig(uut):
    cmd=\
            '''
            fabric forwarding anycast-gateway-mac 0000.2222.3333
            feature ospf
            feature pim
            no router ospf 100
            router ospf 100
            router-id {rid}
            ip pim rp-address {pim_rp_address} group-list 224.0.0.0/4
            '''
    try:
        uut.configure(cmd.format(rid=rid,pim_rp_address=pim_rp_address))
    except:
        log.error('OSPF config failed for node',uut)

def leafPimConfig(uut):
    cmd=\
            '''
            fabric forwarding anycast-gateway-mac 0000.2222.3333
            feature ospf
            feature pim
            no router ospf 100
            router ospf 100
            router-id {rid}
            ip pim rp-address {pim_rp_address} group-list 224.0.0.0/4
            '''
    try:
        uut.configure(cmd.format(rid=rid,pim_rp_address=pim_rp_address))
    except:
        log.error('OSPF config failed for node',uut)


def l3UnnumberedIntfConf(uut,intf_list):
    for intf in intf_list:
        cmd=\
                '''
                default interface {intf}
                interf {intf}
                description VTEP_SPINE
                no switchport
                mtu 9216
                logging event port link-status
                medium p2p
                no ip redirects
                ip unnumbered loopback1
                ip ospf network point-to-point
                ip router ospf 100 area 0.0.0.0
                ip pim sparse-mode
                no shutdown
                '''
        try:
            uut.configure(cmd.format(intf=intf))
        except:
            log.error('Uplink interface config failed for node',uut,intf)


def AccesPortconfigs(uut,intf,vlan_range):
    cmd = """\
    default interface {intf}
    interface {intf}
    switchport
    shut
    #mtu 9216
    switchport mode trunk
    switchport trunk allowed vlan {vlan_range}
    spanning-tree port type edge trunk
    spanning-tree bpdufilter enable
    sleep 1
    no shut
    """
    try:
        uut.configure(cmd.format(intf=intf,vlan_range=vlan_range))
    except:
        log.error('AccesPortconfigs config failed for node',uut,intf)

def ConfigLoopback(uut,interface_id,ipv4,ipv4_sec):
    if not 'Nil' in ipv4_sec:
        config_str = \
            """
            no interf {interface_id}
            interf {interface_id}
            no ip add
            ip add {ipv4}
            ip add {ipv4_sec} second
            descr NVE loopback
            no shut
            """
        try:
            uut.configure(config_str.format(interface_id=interface_id,ipv4=ipv4,ipv4_sec=ipv4_sec))
        except:
            log.error('Loop Config Failed on UUT',uut)

    else:
        config_str = \
            """
            no interf {interface_id}
            interf {interface_id}
            no ip add
            ip add {ipv4}
            no shut
            """
        try:
            uut.configure(config_str.format(interface_id=interface_id,ipv4=ipv4))
        except:
            log.error('Loop Config Failed on UUT',uut)
