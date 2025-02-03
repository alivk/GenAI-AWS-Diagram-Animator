import boto3
import json
import streamlit as st
import re

def get_bedrock_credentials():
    secrets_client = boto3.client('secretsmanager')
    secret_name = "bedrocksecrets"
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secrets = json.loads(response['SecretString'])
        return {
            'region_name': secrets.get('AWS_REGION'),
            'aws_access_key_id': secrets.get('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': secrets.get('AWS_SECRET_ACCESS_KEY'),
            'kendra_index_id': secrets.get('AWS_KENDRA_INDEX_ID'),
            'session_secret': secrets.get('SESSION_SECRET'),
            'session_secret_bdm1': secrets.get('SESSION_SECRET_BDM1'),
            'session_secret_bmd2': secrets.get('SESSION_SECRET_BMD2'),
            'session_secret_instructor1': secrets.get('SESSION_SECRET_INSTRUCTOR1'),
            'session_secret_instructor2': secrets.get('SESSION_SECRET_INSTRUCTOR2')
        }
    except Exception as e:
        st.error(f"Error retrieving Bedrock credentials: {e}")
        return None

def list_available_models():
    claude_models = [
        ("anthropic.claude-3-haiku-20240307-v1:0", "Claude 3 Haiku 1.0"),
        ("anthropic.claude-v2", "Claude 2.0"),
        ("anthropic.claude-v2:1", "Claude 2.1"),
        ("anthropic.claude-3-sonnet-20240229-v1:0", "Claude 3 Sonnet 1.0"),
        ("anthropic.claude-3-5-sonnet-20240620-v1:0", "Claude 3.5 Sonnet 1.0"),
        ("anthropic.claude-instant-v1", "Claude Instant 1.x")
    ]
    return claude_models

def invoke_bedrock_model(prompt, access_key, secret_key, model_id):
    try:
        bedrock_client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='us-east-1'
        )

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        })

        response = bedrock_client.invoke_model_with_response_stream(
            modelId=model_id,
            body=body,
        )

        stream = response.get("body")
        parsed_response = ""

        for event in stream:
            chunk = event.get('chunk')
            if chunk:
                message = json.loads(chunk.get("bytes").decode())
                if "content_block_delta" in message.get('type', ''):
                    parsed_response += message['delta'].get("text", "")
                elif "message_stop" in message.get('type', ''):
                    break

        return parsed_response
    except Exception as e:
        st.error(f"Error in invoking model: {e}")
        return "Response not available due to API error."

def summarize_markdown(markdown_content):
    if markdown_content.strip():
        summarized_content = markdown_content[:500] + "..."
        return summarized_content
    else:
        return "No insights available from the provided learning resources."

def parse_diagram_spec(text):
    """Parse the diagram specification from the prompt text"""
    nodes = []
    connections = []
    animations = []
    
    current_section = None
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('['):
            current_section = line[1:-1].lower()
            continue
            
        if current_section == 'diagram nodes':
            if ' - ' in line:
                node_type, node_name = line.split(' - ', 1)
                nodes.append((node_type.strip(), node_name.strip()))
                
        elif current_section == 'diagram connection':
            connectors = [
                '~~', '~>', '==', '=>', '--', '->', 'to>', ' to>', ' to ', '>>'
            ]
            for c in connectors:
                if c in line:
                    connector = c
                    source, target = line.split(c, 1)
                    connections.append((source.strip(), target.strip(), connector))
                    break
                
        elif current_section == 'animation':
            # Handle all connection types in animations
            connectors = ['~~', '~>', '==', '=>', '--', '->', ' to> ', ' to ', '>>']
            for c in connectors:
                if c in line:
                    source, target = line.split(c, 1)
                    animations.append((source.strip(), target.strip()))
                    break
                
    return nodes, connections, animations

def generate_diagram(nodes, connections, animations=None):
    """Generate a Graphviz diagram with flowing pipe animations"""
    from graphviz import Digraph
    import re

    dot = Digraph(engine='dot')
    dot.attr(
        rankdir='LR', 
        splines='spline', 
        bgcolor='transparent', 
        nodesep='6', 
        ranksep='6',
        size='8,6!'
    )
    
    # Define node appearance by type.
    node_shapes = {
        'EC2': ('box', '#E3F2FD', '#1976D2'),
        'ELB': ('ellipse', '#F1F8E9', '#7CB342'),
        'RDS': ('cylinder', '#FFEBEE', '#D32F2F'),
        'S3': ('folder', '#E8F5E9', '#388E3C')
    }
    
    for node_type, node_name in nodes:
        shape, fill, color = node_shapes.get(node_type, ('box', '#FFFFFF', '#000000'))
        dot.node(node_name, node_name, 
                 shape=shape, 
                 style='filled,rounded',
                 fillcolor=fill,
                 color=color,
                 fontcolor=color,
                 penwidth='2',
                 fontname='Arial',
                 fontsize='12',
                 margin='0.1')
    
    # Optionally force a specific node (here LoadBalancerA) to the same rank.
    if any(node_name == 'LoadBalancerA' for _, node_name in nodes):
        with dot.subgraph() as s:
            s.attr(rank='same')
            s.node('LoadBalancerA')
    
    # Add edges. For edges that should be animated, add an explicit id.
    for source, target in connections:
        is_animated = False
        if animations:
            is_animated = (source, target) in animations
        if is_animated:
            # Create an id by replacing any spaces (ids should not contain spaces).
            edge_id = f"edge_{source}_{target}".replace(" ", "_")
            dot.edge(source, target,
                     color='#FF5722',
                     penwidth='3',
                     arrowsize='1.2',
                     arrowhead='vee',
                     style='bold',
                     # Pass the id attribute (Graphviz will output it in the SVG)
                     id=edge_id)
        else:
            dot.edge(source, target,
                     color='#4CAF50',
                     penwidth='3',
                     arrowsize='1.2',
                     arrowhead='vee',
                     style='bold')
    
    # Generate SVG content with proper coordinate system
    svg_content = dot.pipe(format='svg').decode('utf-8')
    
    # Remove Graphviz transformations and normalize coordinates
    svg_content = re.sub(r'transform="[^"]+"', '', svg_content)
    svg_content = re.sub(r'<g id="graph\d+"[^>]*>', '', svg_content)
    svg_content = svg_content.replace('</g>', '', 1)
    
    # Extract and transform all elements
    paths = re.findall(r'<[^>]+>', svg_content)
    
    # Generate full SVG document with proper layering
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" viewBox="0 0 800 600"
     xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink">
    <defs>
        <linearGradient id="gradient">
            <stop offset="0%" stop-color="white" stop-opacity="0"/>
            <stop offset="40%" stop-color="white" stop-opacity="1"/>
            <stop offset="60%" stop-color="white" stop-opacity="1"/>
            <stop offset="100%" stop-color="white" stop-opacity="0"/>
        </linearGradient>
        <mask id="gradient-mask">
            <rect width="200%" height="100%" fill="url(#gradient)">
                <animate attributeName="x" from="-100%" to="100%" 
                         dur="3s" repeatCount="indefinite"/>
            </rect>
        </mask>
    </defs>

    <!-- Background connections -->
    <g id="background-connections">
        {' '.join([
            re.sub(r'stroke="#ff5722"', 'stroke="#EDEBEB"', p, flags=re.IGNORECASE)
            for p in paths if 'fill="none"' in p
        ])}
    </g>

    <!-- Animated connections -->
    <g id="animated-connections">
        {' '.join([
            re.sub(r'stroke="#ff5722"', 'stroke="#FB5844" mask="url(#gradient-mask)"', p, flags=re.IGNORECASE)
            for p in paths if 'fill="none"' in p and re.search(r'stroke="#ff5722"', p, re.IGNORECASE)
        ])}
    </g>

    <!-- Nodes -->
    <g id="nodes" transform="translate(0,600) scale(1,-1)">
        {' '.join([
            p for p in paths 
            if 'fill="#' in p and 'fill="none"' not in p
        ])}
    </g>
</svg>'''
