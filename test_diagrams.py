# diagrams library installation test

try:
    from diagrams import Diagram, Cluster, Edge
    from diagrams.aws.compute import EC2
    from diagrams.aws.database import RDS
    from diagrams.aws.storage import S3
    from diagrams.aws.network import ELB, CloudFront
    from diagrams.aws.security import ACM, WAF
    from diagrams.aws.storage import EFS
    from diagrams.aws.database import ElastiCache
    
    print("SUCCESS: diagrams library installed!")
    print("SUCCESS: AWS components imported!")
    
    # Test diagram creation
    with Diagram("Test", filename="test_diagram", show=False):
        ec2 = EC2("EC2")
        rds = RDS("RDS")
        ec2 >> rds
    
    print("SUCCESS: Test diagram created!")
    print("FILE: test_diagram.png created")
    
except ImportError as e:
    print(f"ERROR: diagrams library import error: {e}")
    print("SOLUTION: pip install diagrams")
except Exception as e:
    print(f"ERROR: Diagram creation error: {e}")
    print("SOLUTION: Install Graphviz from https://graphviz.org/download/")