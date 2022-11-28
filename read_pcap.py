import binascii
import json
import re

from scapy.all import *

from Compare import align, compare_MMS, get_domainID, get_itemID
from myParser import Parser as myParser


def Read_and_Parse_Encapsulation(pkt):
    all_packet_data = {}
    content = binascii.hexlify(bytes(pkt)).decode()
    # print(content)
    all_packet_data['IP'] = {
        'src_IP': content[54:62], 'dest_IP': content[62:70]}
    find_cotp = re.search('0300....02f080', content)  # search COTP
    if (find_cotp == None):
        return {}
    cotp_index = find_cotp.span()
    content = content[cotp_index[0]:]

    start_index = 0
    tkpt_length = int(content[start_index+4:start_index+8], 16)*2
    tpkt_payload = content[start_index:start_index+tkpt_length]

    TPKT = [tpkt_payload[:2], tpkt_payload[2:4], tpkt_payload[4:8]]
    all_packet_data.update({'TPKT': TPKT})
    # print("TKPT", TPKT)
    COTP = [tpkt_payload[8:10], tpkt_payload[10:12], tpkt_payload[12:14]]
    all_packet_data.update({'COTP': COTP})
    # print("COTP", COTP)
    ISO8327A = [tpkt_payload[14:16], tpkt_payload[16:18]]
    all_packet_data.update({'ISO8327A': ISO8327A})
    # print("ISO8327A", ISO8327A)
    ISO8327B = [tpkt_payload[18:20], tpkt_payload[20:22]]
    all_packet_data.update({'ISO8327B': ISO8327B})
    # print("ISO8327B", ISO8327B)

    # print("ISO8823 begin with 61", tpkt_payload[22:24])

    # print("ISO8823 payload", tpkt_payload[24:])

    rest, ISO8823 = myParser(tpkt_payload[22:], "ISO8823")
    all_packet_data.update(ISO8823[0])

    rest, MMS = myParser(rest, "MMS")
    all_packet_data.update(MMS[0])
    return all_packet_data



realSystem = sniff(offline='s1-morning.pcap',
                   filter='tcp')

DigitalTwins = sniff(offline='situation1_morning_again.pcap',
                     filter='tcp')

# pkt = rdpcap('DegitalTwins.pcap')
# print("1.", all_packets[0])
# content = binascii.hexlify(bytes(all_packets[0])).decode()
# print("2.", content)


def Parse_PCAP(pcapfile_scapy):
    result_list = []
    for index, i in enumerate(pcapfile_scapy):
        output = Read_and_Parse_Encapsulation(i)
        if (len(output) != 0):
            result_list.append(output)
    return result_list


realSystem_list = Parse_PCAP(realSystem)
DigitalTwins_list = Parse_PCAP(DigitalTwins)

fail = 0
fail_list = []
for index, i in enumerate(DigitalTwins_list):
    print(index)
    try:
        digitaltwins_temp = compare_MMS(i, 'MMS')
        realsystem_temp = compare_MMS(realSystem_list[index], 'MMS')

        digitaltwins_itemID = get_itemID(digitaltwins_temp)
        realsystem_itemID = get_itemID(realsystem_temp)

        digitaltwins_domainID = get_domainID(digitaltwins_temp)
        realsystem_domainID = get_domainID(realsystem_temp)
        print('DigitalTwins:', digitaltwins_temp)
        print('RealSystem:', realsystem_temp)
    except Exception as e:
        print(e)
        print(i)
        fail += 1
        fail_list.append((e, i))
print(fail, fail/len(DigitalTwins_list))

with open('packet_result.json', "w") as file:
    json.dump(fail_list, file, indent=2)

chance = 3
while (chance > 0):
    try:
        print(DigitalTwins_list[0])
        print(realSystem_list[0])
        chance -= 1
        DigitalTwins_list = DigitalTwins_list[1:]
        realSystem_list, DigitalTwins_list = align(realSystem_list, DigitalTwins_list)
        pass
    except Exception as e:
        pass

    # compare
    #   module lcs
    chance -= 1
    pass


# a = Ether()/IP(dst='192.168.2.13')/TCP()/"test scapy by python"
# sendp(a)
# a = IP(dst='192.168.2.13')/TCP()/"test scapy by python"
# all_packets[0].show()
# sendp(pkt[0])
# for i in pkt:
#     sendp(i)
# send(pkt[1])
# print(a)
# sniff(iface="en0", filter='tcp and dst host 192.168.2.13 and src host 192.168.2.202', prn=lambda x: x.show())
# all_packets = sniff(offline = 'abb es_open ds_open cb_open2close_pcap.pcap', filter='dst host 192.168.2.13', prn=lambda x: x.summary() ) # 效率好
# print(all_packets)
