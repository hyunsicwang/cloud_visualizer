import streamlit as st
import urllib.parse
import base64
from datetime import datetime

# Draw.io XML을 iframe에 로드하는 함수
def load_drawio_with_xml(xml_content):
    if xml_content:
        try:
            # 간단한 URL 인코딩 사용
            encoded_xml = urllib.parse.quote(xml_content, safe='')
            
            # Draw.io iframe
            iframe_html = f"""
            <iframe
            src="https://embed.diagrams.net/?embed=1&ui=atlas&xml={encoded_xml}"
            width="100%"
            height="800"
            frameborder="0">
            </iframe>
            """
            return iframe_html
        except Exception as e:
            return f"<p>구성도 로드 오류: {e}</p>"
    else:
        return "<p>구성도를 생성할 수 없습니다.</p>"

# AWS 리소스로 Draw.io XML 생성 (서브넷별 EC2 정확 배치)
def generate_aws_drawio_xml(project_name, aws_data):
    try:
        cells = []
        cell_id = 2
        connections = []
        
        # VPC 정보 추출
        vpc_name = "VPC"
        if 'VPC' in aws_data and hasattr(aws_data['VPC'], '__len__') and len(aws_data['VPC']) > 0:
            vpc_name = aws_data['VPC'].iloc[0]['VPC Name'] if 'VPC Name' in aws_data['VPC'].columns else "VPC"
        
        # VPC 컴포넌트
        cells.append(f'<mxCell id="{cell_id}" value="{vpc_name}" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#248814;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#AAB7B8;dashed=0;" vertex="1" parent="1"><mxGeometry x="80" y="120" width="1200" height="700" as="geometry" /></mxCell>')
        vpc_id = cell_id
        cell_id += 1
        
        # Internet Gateway 정보
        igw_name = "Internet Gateway"
        if 'Internet Gateway' in aws_data and hasattr(aws_data['Internet Gateway'], '__len__') and len(aws_data['Internet Gateway']) > 0:
            igw_name = aws_data['Internet Gateway'].iloc[0]['Name'] if 'Name' in aws_data['Internet Gateway'].columns else "Internet Gateway"
        
        cells.append(f'<mxCell id="{cell_id}" value="{igw_name}" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.internet_gateway;" vertex="1" parent="1"><mxGeometry x="641" y="40" width="78" height="78" as="geometry" /></mxCell>')
        igw_id = cell_id
        cell_id += 1
        
        # 서브넷 정보 추출 및 AZ 그룹화
        az_subnets = {}
        if 'Subnet' in aws_data and hasattr(aws_data['Subnet'], '__len__') and len(aws_data['Subnet']) > 0:
            for _, subnet in aws_data['Subnet'].iterrows():
                az = subnet.get('Availability Zone', 'Unknown')
                if az not in az_subnets:
                    az_subnets[az] = {'public': [], 'private': []}
                
                subnet_type = 'public' if 'public' in subnet.get('Name', '').lower() else 'private'
                az_subnets[az][subnet_type].append(subnet)
        
        # AZ 및 서브넷 생성
        az_positions = [(150, 180, 500, 300), (750, 180, 500, 300)]
        az_ids = {}
        subnet_ids = {}
        
        for i, (az, subnets) in enumerate(az_subnets.items()):
            if i >= 2: break
            x, y, w, h = az_positions[i]
            
            # AZ 그룹
            cells.append(f'<mxCell id="{cell_id}" value="{az}" style="fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;fontStyle=0;fontColor=#147EBA;whiteSpace=wrap;html=1;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" /></mxCell>')
            az_ids[az] = cell_id
            cell_id += 1
            
            # Public Subnet
            if subnets['public']:
                subnet = subnets['public'][0]
                subnet_name = subnet.get('Name', f'Public Subnet {i+1}')
                cells.append(f'<mxCell id="{cell_id}" value="{subnet_name}" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=10;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#00A4A6;fillColor=#E6F3FF;verticalAlign=top;align=left;spacingLeft=30;fontColor=#147EBA;dashed=0;" vertex="1" parent="1"><mxGeometry x="{x+20}" y="{y+30}" width="{w-40}" height="80" as="geometry" /></mxCell>')
                subnet_ids[f'public_{i}'] = cell_id
                cell_id += 1
            
            # Private Subnet
            if subnets['private']:
                subnet = subnets['private'][0]
                subnet_name = subnet.get('Name', f'Private Subnet {i+1}')
                cells.append(f'<mxCell id="{cell_id}" value="{subnet_name}" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=10;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#00A4A6;fillColor=#FFF2E6;verticalAlign=top;align=left;spacingLeft=30;fontColor=#147EBA;dashed=0;" vertex="1" parent="1"><mxGeometry x="{x+20}" y="{y+130}" width="{w-40}" height="140" as="geometry" /></mxCell>')
                subnet_ids[f'private_{i}'] = cell_id
                cell_id += 1
        
        # ALB 생성
        alb_id = None
        if 'ELB' in aws_data and hasattr(aws_data['ELB'], '__len__') and len(aws_data['ELB']) > 0:
            alb_name = aws_data['ELB'].iloc[0]['Load Balancer'] if 'Load Balancer' in aws_data['ELB'].columns else "ALB"
            cells.append(f'<mxCell id="{cell_id}" value="{alb_name}" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=10;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.application_load_balancer;" vertex="1" parent="1"><mxGeometry x="500" y="150" width="78" height="78" as="geometry" /></mxCell>')
            alb_id = cell_id
            cell_id += 1
        
        # EC2 인스턴스 생성
        ec2_ids = []
        if 'EC2' in aws_data and hasattr(aws_data['EC2'], '__len__') and len(aws_data['EC2']) > 0:
            for i, (_, ec2) in enumerate(aws_data['EC2'].iterrows()):
                if i >= 4: break
                ec2_name = ec2.get('Name', f'EC2-{i+1}')
                
                # 위치 계산 (Private Subnet에 배치)
                subnet_idx = i % 2
                x_pos = 200 + (subnet_idx * 600) + (i // 2) * 100
                y_pos = 350 + (i % 2) * 60
                
                cells.append(f'<mxCell id="{cell_id}" value="{ec2_name}" style="sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=10;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;" vertex="1" parent="1"><mxGeometry x="{x_pos}" y="{y_pos}" width="48" height="48" as="geometry" /></mxCell>')
                ec2_ids.append(cell_id)
                cell_id += 1
        
        # NAT Gateway 생성
        if 'NAT Gateway' in aws_data and hasattr(aws_data['NAT Gateway'], '__len__') and len(aws_data['NAT Gateway']) > 0:
            for i, (_, nat) in enumerate(aws_data['NAT Gateway'].iterrows()):
                if i >= 2: break
                nat_name = nat.get('Name', f'NAT Gateway {i+1}')
                x_pos = 220 + (i * 600)
                y_pos = 240
                
                cells.append(f'<mxCell id="{cell_id}" value="{nat_name}" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=10;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.nat_gateway;" vertex="1" parent="1"><mxGeometry x="{x_pos}" y="{y_pos}" width="48" height="48" as="geometry" /></mxCell>')
                cell_id += 1
        
        # RDS 생성
        rds_id = None
        if 'RDS' in aws_data and hasattr(aws_data['RDS'], '__len__') and len(aws_data['RDS']) > 0:
            rds_name = aws_data['RDS'].iloc[0]['DB Instance'] if 'DB Instance' in aws_data['RDS'].columns else "RDS"
            cells.append(f'<mxCell id="{rds_id}" value="{rds_name}" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#C925D1;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=10;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.rds_instance;" vertex="1" parent="1"><mxGeometry x="500" y="550" width="78" height="78" as="geometry" /></mxCell>')
            rds_id = cell_id
            cell_id += 1
        
        # S3 생성
        if 'S3' in aws_data and hasattr(aws_data['S3'], '__len__') and len(aws_data['S3']) > 0:
            s3_name = aws_data['S3'].iloc[0]['Bucket Name'] if 'Bucket Name' in aws_data['S3'].columns else "S3"
            cells.append(f'<mxCell id="{cell_id}" value="{s3_name}" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#7AA116;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=10;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.s3;" vertex="1" parent="1"><mxGeometry x="1320" y="350" width="78" height="78" as="geometry" /></mxCell>')
            cell_id += 1
        
        # 연결선 생성
        if alb_id and ec2_ids:
            for ec2_id in ec2_ids:
                connections.append(f'<mxCell id="{cell_id}" value="" style="endArrow=classic;html=1;rounded=0;" edge="1" parent="1" source="{alb_id}" target="{ec2_id}"><mxGeometry width="50" height="50" relative="1" as="geometry"><mxPoint x="500" y="300" as="sourcePoint" /><mxPoint x="550" y="250" as="targetPoint" /></mxGeometry></mxCell>')
                cell_id += 1
        
        if igw_id and alb_id:
            connections.append(f'<mxCell id="{cell_id}" value="" style="endArrow=classic;html=1;rounded=0;" edge="1" parent="1" source="{igw_id}" target="{alb_id}"><mxGeometry width="50" height="50" relative="1" as="geometry"><mxPoint x="500" y="200" as="sourcePoint" /><mxPoint x="550" y="150" as="targetPoint" /></mxGeometry></mxCell>')
            cell_id += 1
        
        # XML 생성
        all_cells = cells + connections
        cells_xml = '\n        '.join(all_cells)
        
        xml_content = f"""<mxfile host="embed.diagrams.net">
  <diagram name="{project_name} AWS Architecture" id="aws-diagram">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1500" pageHeight="900">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        {cells_xml}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""
        
        return xml_content.strip()
        
    except Exception as e:
        st.error(f"AWS 구성도 생성 오류: {e}")
        return None