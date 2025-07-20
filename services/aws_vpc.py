import streamlit as st
import pandas as pd

# VPC 조회
def get_vpcs(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_vpcs()
        vpcs = []
        for vpc in response['Vpcs']:
            name = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            vpcs.append({
                'VPC ID': vpc['VpcId'],
                'Name': name,
                'CIDR Block': vpc['CidrBlock'],
                'State': vpc['State'],
                'Default': vpc['IsDefault']
            })
        return pd.DataFrame(vpcs)
    except Exception as e:
        st.error(f"VPC 조회 오류: {e}")
        return pd.DataFrame()

# Subnet 조회
def get_subnets(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_subnets()
        subnets = []
        for subnet in response['Subnets']:
            name = next((tag['Value'] for tag in subnet.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            subnets.append({
                'Subnet ID': subnet['SubnetId'],
                'Name': name,
                'VPC ID': subnet['VpcId'],
                'CIDR Block': subnet['CidrBlock'],
                'Availability Zone': subnet['AvailabilityZone'],
                'Available IPs': subnet['AvailableIpAddressCount'],
                'State': subnet['State']
            })
        return pd.DataFrame(subnets)
    except Exception as e:
        st.error(f"Subnet 조회 오류: {e}")
        return pd.DataFrame()

# Internet Gateway 조회
def get_internet_gateways(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_internet_gateways()
        igws = []
        for igw in response['InternetGateways']:
            name = next((tag['Value'] for tag in igw.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            attachments = ', '.join([att['VpcId'] for att in igw.get('Attachments', [])])
            igws.append({
                'IGW ID': igw['InternetGatewayId'],
                'Name': name,
                'State': igw['Attachments'][0]['State'] if igw.get('Attachments') else 'detached',
                'Attached VPCs': attachments or 'None'
            })
        return pd.DataFrame(igws)
    except Exception as e:
        st.error(f"Internet Gateway 조회 오류: {e}")
        return pd.DataFrame()

# NAT Gateway 조회
def get_nat_gateways(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_nat_gateways()
        nat_gws = []
        for nat in response['NatGateways']:
            name = next((tag['Value'] for tag in nat.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            # Public IP 추출
            public_ip = 'N/A'
            for address in nat.get('NatGatewayAddresses', []):
                if 'PublicIp' in address:
                    public_ip = address['PublicIp']
                    break
            
            nat_gws.append({
                'NAT Gateway ID': nat['NatGatewayId'],
                'Name': name,
                'VPC ID': nat['VpcId'],
                'Subnet ID': nat['SubnetId'],
                'Public IP': public_ip,
                'State': nat['State'],
                'Type': nat.get('ConnectivityType', 'public')
            })
        return pd.DataFrame(nat_gws)
    except Exception as e:
        st.error(f"NAT Gateway 조회 오류: {e}")
        return pd.DataFrame()

# VPN Gateway 조회
def get_vpn_gateways(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_vpn_gateways()
        vpn_gws = []
        for vpn in response['VpnGateways']:
            name = next((tag['Value'] for tag in vpn.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            attachments = ', '.join([att['VpcId'] for att in vpn.get('VpcAttachments', [])])
            vpn_gws.append({
                'VPN Gateway ID': vpn['VpnGatewayId'],
                'Name': name,
                'Type': vpn['Type'],
                'State': vpn['State'],
                'Attached VPCs': attachments or 'None'
            })
        return pd.DataFrame(vpn_gws)
    except Exception as e:
        st.error(f"VPN Gateway 조회 오류: {e}")
        return pd.DataFrame()

# Site-to-Site VPN 연결 조회
def get_vpn_connections(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_vpn_connections()
        vpn_connections = []
        for vpn in response['VpnConnections']:
            name = next((tag['Value'] for tag in vpn.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            
            # 터널 정보 추출
            tunnel_info = []
            for i, tunnel in enumerate(vpn.get('VgwTelemetry', []), 1):
                status = tunnel.get('Status', 'N/A')
                tunnel_info.append(f"터널{i}: {status}")
            
            # 정적 라우팅 CIDR 추출
            static_routes = []
            for route in vpn.get('Routes', []):
                if 'DestinationCidrBlock' in route:
                    static_routes.append(route['DestinationCidrBlock'])
            
            vpn_connections.append({
                'VPN Connection ID': vpn['VpnConnectionId'],
                'Name': name,
                'State': vpn['State'],
                'VPN Gateway ID': vpn.get('VpnGatewayId', 'N/A'),
                'Customer Gateway ID': vpn.get('CustomerGatewayId', 'N/A'),
                'Type': vpn.get('Type', 'N/A'),
                'Tunnel Status': ', '.join(tunnel_info),
                'Static Routes': ', '.join(static_routes) if static_routes else 'N/A'
            })
        return pd.DataFrame(vpn_connections)
    except Exception as e:
        st.error(f"Site-to-Site VPN 조회 오류: {e}")
        return pd.DataFrame()

# Transit Gateway 조회
def get_transit_gateways(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_transit_gateways()
        tgws = []
        for tgw in response['TransitGateways']:
            name = next((tag['Value'] for tag in tgw.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            tgws.append({
                'Transit Gateway ID': tgw['TransitGatewayId'],
                'Name': name,
                'State': tgw['State'],
                'Owner ID': tgw['OwnerId'],
                'Default Route Table': tgw.get('Options', {}).get('DefaultRouteTableAssociation', 'N/A')
            })
        return pd.DataFrame(tgws)
    except Exception as e:
        st.error(f"Transit Gateway 조회 오류: {e}")
        return pd.DataFrame()

# VPC Peering Connection 조회
def get_vpc_peering_connections(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_vpc_peering_connections()
        peerings = []
        for peer in response['VpcPeeringConnections']:
            name = next((tag['Value'] for tag in peer.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            peerings.append({
                'Peering Connection ID': peer['VpcPeeringConnectionId'],
                'Name': name,
                'Requester VPC': peer['RequesterVpcInfo']['VpcId'],
                'Accepter VPC': peer['AccepterVpcInfo']['VpcId'],
                'Status': peer['Status']['Code'],
                'Requester Region': peer['RequesterVpcInfo'].get('Region', 'N/A'),
                'Accepter Region': peer['AccepterVpcInfo'].get('Region', 'N/A')
            })
        return pd.DataFrame(peerings)
    except Exception as e:
        st.error(f"VPC Peering 조회 오류: {e}")
        return pd.DataFrame()

# Customer Gateway 조회
def get_customer_gateways(session):
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_customer_gateways()
        gateways = []
        for cgw in response['CustomerGateways']:
            name = next((tag['Value'] for tag in cgw.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            gateways.append({
                'Customer Gateway ID': cgw['CustomerGatewayId'],
                'Name': name,
                'IP Address': cgw.get('IpAddress', 'N/A'),
                'BGP ASN': cgw.get('BgpAsn', 'N/A'),
                'State': cgw['State']
            })
        return pd.DataFrame(gateways)
    except Exception as e:
        st.error(f"Customer Gateway 조회 오류: {e}")
        return pd.DataFrame()