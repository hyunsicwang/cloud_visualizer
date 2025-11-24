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
            vpc_name = aws_data['VPC'].iloc[0]['Name'] if 'Name' in aws_data['VPC'].columns else "VPC"
        
        # VPC 컴포넌트
        cells.append(f'<mxCell id="{cell_id}" value="{vpc_name}" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#248814;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#AAB7B8;dashed=0;" vertex="1" parent="1"><mxGeometry x="80" y="120" width="1400" height="800" as="geometry" /></mxCell>')
        vpc_id = cell_id
        cell_id += 1
        
        # Internet Gateway 정보
        igw_name = "Internet Gateway"
        if 'Internet Gateway' in aws_data and hasattr(aws_data['Internet Gateway'], '__len__') and len(aws_data['Internet Gateway']) > 0:
            igw_name = aws_data['Internet Gateway'].iloc[0]['Name'] if 'Name' in aws_data['Internet Gateway'].columns else "Internet Gateway"
        
        cells.append(f'<mxCell id="{cell_id}" value="{igw_name}" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.internet_gateway;" vertex="1" parent="1"><mxGeometry x="741" y="40" width="78" height="78" as="geometry" /></mxCell>')
        igw_id = cell_id
        cell_id += 1
        
        # 서브넷 정보 추출 및 매핑
        subnet_mapping = {}
        subnet_positions = {}
        
        if 'Subnet' in aws_data and hasattr(aws_data['Subnet'], '__len__') and len(aws_data['Subnet']) > 0:
            # AZ별로 서브넷 그룹화
            az_subnets = {}
            for _, subnet in aws_data['Subnet'].iterrows():
                az = subnet.get('Availability Zone', 'Unknown')
                subnet_id = subnet.get('Subnet ID', '')
                subnet_name = subnet.get('Name', subnet_id)
                
                if az not in az_subnets:
                    az_subnets[az] = {'public': [], 'private': []}
                
                subnet_type = 'public' if 'public' in subnet_name.lower() else 'private'
                az_subnets[az][subnet_type].append({
                    'id': subnet_id,
                    'name': subnet_name,
                    'data': subnet
                })
            
            # AZ 및 서브넷 생성
            az_count = len(az_subnets)
            az_width = 350
            total_width = az_count * az_width + (az_count - 1) * 50
            start_x = 150
            
            for i, (az, subnets) in enumerate(az_subnets.items()):
                x = start_x + i * (az_width + 50)
                y = 180
                
                # AZ 그룹
                cells.append(f'<mxCell id="{cell_id}" value="{az}" style="fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;fontStyle=0;fontColor=#147EBA;whiteSpace=wrap;html=1;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{az_width}" height="400" as="geometry" /></mxCell>')
                cell_id += 1
                
                # Public Subnet
                public_y = y + 30
                for j, subnet in enumerate(subnets['public']):
                    subnet_y = public_y + j * 90
                    subnet_name = subnet['name']
                    cells.append(f'<mxCell id="{cell_id}" value="{subnet_name}" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=10;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#00A4A6;fillColor=#E6F3FF;verticalAlign=top;align=left;spacingLeft=30;fontColor=#147EBA;dashed=0;" vertex="1" parent="1"><mxGeometry x="{x+20}" y="{subnet_y}" width="{az_width-40}" height="80" as="geometry" /></mxCell>')
                    subnet_mapping[subnet['id']] = {
                        'cell_id': cell_id,
                        'x': x + 20,
                        'y': subnet_y,
                        'width': az_width - 40,
                        'height': 80,
                        'type': 'public'
                    }
                    cell_id += 1
                
                # Private Subnet
                private_y = y + 200
                for j, subnet in enumerate(subnets['private']):
                    subnet_y = private_y + j * 90
                    subnet_name = subnet['name']
                    cells.append(f'<mxCell id="{cell_id}" value="{subnet_name}" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=10;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;strokeColor=#00A4A6;fillColor=#FFF2E6;verticalAlign=top;align=left;spacingLeft=30;fontColor=#147EBA;dashed=0;" vertex="1" parent="1"><mxGeometry x="{x+20}" y="{subnet_y}" width="{az_width-40}" height="80" as="geometry" /></mxCell>')
                    subnet_mapping[subnet['id']] = {
                        'cell_id': cell_id,
                        'x': x + 20,
                        'y': subnet_y,
                        'width': az_width - 40,
                        'height': 80,
                        'type': 'private'
                    }
                    cell_id += 1
        
        # ALB 생성
        alb_id = None
        if 'ELB' in aws_data and hasattr(aws_data['ELB'], '__len__') and len(aws_data['ELB']) > 0:
            alb_name = aws_data['ELB'].iloc[0]['Load Balancer'] if 'Load Balancer' in aws_data['ELB'].columns else "ALB"
            cells.append(f'<mxCell id="{cell_id}" value="{alb_name}" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=10;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.application_load_balancer;" vertex="1" parent="1"><mxGeometry x="700" y="150" width="78" height="78" as="geometry" /></mxCell>')
            alb_id = cell_id
            cell_id += 1
        
        # 모든 EC2 인스턴스를 서브넷별로 배치
        ec2_ids = []
        subnet_ec2_count = {}
        
        if 'EC2' in aws_data and hasattr(aws_data['EC2'], '__len__') and len(aws_data['EC2']) > 0:
            for _, ec2 in aws_data['EC2'].iterrows():
                ec2_name = ec2.get('Name', 'EC2')
                ec2_subnet_id = ec2.get('Subnet ID', '')
                
                if ec2_subnet_id in subnet_mapping:
                    subnet_info = subnet_mapping[ec2_subnet_id]
                    
                    # 서브넷별 EC2 개수 추적
                    if ec2_subnet_id not in subnet_ec2_count:
                        subnet_ec2_count[ec2_subnet_id] = 0
                    
                    # EC2 위치 계산 (서브넷 내에서 배치)
                    ec2_per_row = 4
                    row = subnet_ec2_count[ec2_subnet_id] // ec2_per_row
                    col = subnet_ec2_count[ec2_subnet_id] % ec2_per_row
                    
                    x_pos = subnet_info['x'] + 40 + col * 60
                    y_pos = subnet_info['y'] + 35 + row * 60
                    
                    cells.append(f'<mxCell id="{cell_id}" value="{ec2_name}" style="sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=8;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;" vertex="1" parent="1"><mxGeometry x="{x_pos}" y="{y_pos}" width="40" height="40" as="geometry" /></mxCell>')
                    ec2_ids.append(cell_id)
                    subnet_ec2_count[ec2_subnet_id] += 1
                    cell_id += 1
                else:
                    # 서브넷 정보가 없는 EC2는 기본 위치에 배치
                    x_pos = 200 + (len(ec2_ids) % 4) * 80
                    y_pos = 600 + (len(ec2_ids) // 4) * 60
                    
                    cells.append(f'<mxCell id="{cell_id}" value="{ec2_name}" style="sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=8;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;" vertex="1" parent="1"><mxGeometry x="{x_pos}" y="{y_pos}" width="40" height="40" as="geometry" /></mxCell>')
                    ec2_ids.append(cell_id)
                    cell_id += 1
        
        # NAT Gateway 생성
        if 'NAT Gateway' in aws_data and hasattr(aws_data['NAT Gateway'], '__len__') and len(aws_data['NAT Gateway']) > 0:
            nat_count = 0
            for _, nat in aws_data['NAT Gateway'].iterrows():
                nat_name = nat.get('Name', f'NAT Gateway {nat_count+1}')
                nat_subnet_id = nat.get('Subnet ID', '')
                
                if nat_subnet_id in subnet_mapping:
                    subnet_info = subnet_mapping[nat_subnet_id]
                    x_pos = subnet_info['x'] + 50
                    y_pos = subnet_info['y'] + 20
                else:
                    x_pos = 220 + (nat_count * 200)
                    y_pos = 240
                
                cells.append(f'<mxCell id="{cell_id}" value="{nat_name}" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=10;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.nat_gateway;" vertex="1" parent="1"><mxGeometry x="{x_pos}" y="{y_pos}" width="48" height="48" as="geometry" /></mxCell>')
                nat_count += 1
                cell_id += 1
        
        # RDS 생성
        if 'RDS' in aws_data and hasattr(aws_data['RDS'], '__len__') and len(aws_data['RDS']) > 0:
            rds_count = 0
            for _, rds in aws_data['RDS'].iterrows():
                rds_name = rds.get('DB Instance', f'RDS-{rds_count+1}')
                x_pos = 700 + (rds_count * 100)
                y_pos = 700
                
                cells.append(f'<mxCell id="{cell_id}" value="{rds_name}" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#C925D1;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=10;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.rds_instance;" vertex="1" parent="1"><mxGeometry x="{x_pos}" y="{y_pos}" width="78" height="78" as="geometry" /></mxCell>')
                rds_count += 1
                cell_id += 1
        
        # S3 생성
        if 'S3' in aws_data and hasattr(aws_data['S3'], '__len__') and len(aws_data['S3']) > 0:
            s3_count = 0
            for _, s3 in aws_data['S3'].iterrows():
                s3_name = s3.get('Bucket Name', f'S3-{s3_count+1}')
                x_pos = 1520 + (s3_count * 100)
                y_pos = 350 + (s3_count * 100)
                
                cells.append(f'<mxCell id="{cell_id}" value="{s3_name}" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#7AA116;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=10;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.s3;" vertex="1" parent="1"><mxGeometry x="{x_pos}" y="{y_pos}" width="78" height="78" as="geometry" /></mxCell>')
                s3_count += 1
                cell_id += 1
        
        # 연결선 생성 (ALB에서 EC2로)
        if alb_id and ec2_ids:
            for ec2_id in ec2_ids[:5]:  # 너무 많은 연결선 방지
                connections.append(f'<mxCell id="{cell_id}" value="" style="endArrow=classic;html=1;rounded=0;strokeColor=#666666;" edge="1" parent="1" source="{alb_id}" target="{ec2_id}"><mxGeometry width="50" height="50" relative="1" as="geometry"><mxPoint x="500" y="300" as="sourcePoint" /><mxPoint x="550" y="250" as="targetPoint" /></mxGeometry></mxCell>')
                cell_id += 1
        
        # IGW에서 ALB로 연결
        if igw_id and alb_id:
            connections.append(f'<mxCell id="{cell_id}" value="" style="endArrow=classic;html=1;rounded=0;strokeColor=#666666;" edge="1" parent="1" source="{igw_id}" target="{alb_id}"><mxGeometry width="50" height="50" relative="1" as="geometry"><mxPoint x="500" y="200" as="sourcePoint" /><mxPoint x="550" y="150" as="targetPoint" /></mxGeometry></mxCell>')
            cell_id += 1
        
        # XML 생성
        all_cells = cells + connections
        cells_xml = '\n        '.join(all_cells)
        
        xml_content = f"""<mxfile host="embed.diagrams.net">
  <diagram name="{project_name} AWS Architecture" id="aws-diagram">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1800" pageHeight="1000">
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