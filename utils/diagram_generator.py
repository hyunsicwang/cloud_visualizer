import streamlit as st
import urllib.parse
from datetime import datetime

# Draw.io XML을 iframe에 로드하는 함수
def load_drawio_with_xml(xml_content):
    if xml_content:
        # XML을 URL 인코딩
        encoded_xml = urllib.parse.quote(xml_content)
        
        # Draw.io iframe에 XML 데이터 로드
        iframe_html = f"""
        <iframe
        src="https://embed.diagrams.net/?embed=1&ui=atlas&proto=json&xml={encoded_xml}"
        width="100%"
        height="800"
        frameborder="0">
        </iframe>
        """
        return iframe_html
    else:
        return "<p>구성도를 생성할 수 없습니다.</p>"

# AWS 리소스로 Draw.io XML 생성 (서브넷별 EC2 정확 배치)
def generate_aws_drawio_xml(project_name, aws_data):
    try:
        cell_id = 2
        cells = []
        
        # VPC 컴포넌트 (전체 틀)
        cells.append('<mxCell id="2" value="" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#248814;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#AAB7B8;dashed=0;" vertex="1" parent="1"><mxGeometry x="40" y="120" width="1200" height="800" as="geometry" /></mxCell>')
        cell_id += 1
        
        # VPC 라벨
        cells.append(f'<mxCell id="{cell_id}" value="VPC" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=14;fontStyle=1;fontColor=#248814;" vertex="1" parent="1"><mxGeometry x="50" y="130" width="100" height="30" as="geometry" /></mxCell>')
        cell_id += 1
        
        # Internet Gateway
        cells.append(f'<mxCell id="{cell_id}" value="Internet Gateway" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.internet_gateway;" vertex="1" parent="1"><mxGeometry x="581" y="40" width="78" height="78" as="geometry" /></mxCell>')
        cell_id += 1
        
        # 리소스가 없을 경우
        if len(cells) <= 6:
            cells.append('<mxCell id="50" value="No AWS Resources Found" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=16" vertex="1" parent="1"><mxGeometry x="500" y="400" width="200" height="80" as="geometry" /></mxCell>')
        
        # XML 생성
        cells_xml = '\\n        '.join(cells)
        
        xml_content = f"""<mxfile host="embed.diagrams.net" modified="{datetime.now().isoformat()}Z" agent="5.0" version="22.1.16" etag="aws-diagram" type="embed">
  <diagram name="{project_name} AWS Architecture" id="aws-diagram">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1400" pageHeight="1000" math="0" shadow="0">
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
        st.error(f"Draw.io XML 생성 오류: {e}")
        return None