import streamlit as st
from bedrock_utils import get_bedrock_credentials, list_available_models, invoke_bedrock_model, parse_diagram_spec, generate_diagram
import streamlit.components.v1 as components
import re
import base64

def main():
    st.title("Interactive Architecture Diagram Generator")
    
    # Custom CSS for animations
    st.markdown("""
    <style>
    @keyframes dash {
        to { stroke-dashoffset: -20; }
    }
    .animated-line {
        stroke-dasharray: 5, 5;
        animation: dash 1s linear infinite;
    }
    </style>
    """, unsafe_allow_html=True)

    # Node configuration
    col1, col2 = st.columns(2)
    with col1:
        nodes = st.text_area("Diagram Nodes", 
                           value="[diagram nodes]\n"
                                 "LAYER1 - UserA\n"
                                 "LAYER2 - CloudfrontA\n"
                                 "LAYER2 - ALBA\n"
                                 "LAYER3 - WebServerA\n"
                                 "LAYER3 - WebServerB\n"
                                 "LAYER4 - AppServerA\n"
                                 "LAYER4 - AppServerB\n"
                                 "LAYER5 - DBServerA\n"
                                 "LAYER5 - DBServerB\n",
                           height=150)
    
    with col2:
        connections = st.text_area("Diagram Connections",
                                 value="[diagram connection]\n"
                                       "UserA to> CloudfrontA \n"
                                       "CloudfrontA to> ALBA \n"
                                       "ALBA ~> WebServerA\n"
                                       "ALBA ~> WebServerB\n"
                                       "WebServerA ~> AppServerA\n"
                                       "WebServerA ~> AppServerB\n"
                                       "WebServerB ~> AppServerA\n"
                                       "WebServerB ~> AppServerB\n"
                                       "AppServerA ~> DBServerA\n"
                                       "AppServerB >> DBServerB\n",
                                 height=150)
    
    animations = st.text_area("Animations (Optional)",
                            value="",
                            height=100)

    if st.button("Generate Diagram"):
        # Parse inputs
        parsed_nodes, parsed_conns, parsed_anims = parse_diagram_spec(
            nodes + "\n" + connections + "\n" + animations
        )
        
        # Generate SVG
        svg_content = generate_custom_svg(parsed_nodes, parsed_conns, parsed_anims)
        
        # Display
        st.components.v1.html(svg_content, width=800, height=600)
        
        # Download
        b64 = base64.b64encode(svg_content.encode()).decode()
        href = f'<a href="data:image/svg+xml;base64,{b64}" download="diagram.svg">Download SVG</a>'
        st.markdown(href, unsafe_allow_html=True)

def generate_custom_svg(nodes, connections, animations):
    # Add color palette
    CONNECTION_COLORS = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', 
        '#D4A5A5', '#77CC6D', '#9A94BC', '#FF9F89', '#83E8BA'
    ]
    color_index = 0

    # Layout configuration
    svg_width = 800
    svg_height = 600
    node_width = 120
    node_height = 50
    gap = 50  # Space between tiers
    
    # Group nodes by layer
    layers = {f'LAYER{i}': [] for i in range(1,6)}
    for node_type, label in nodes:
        if node_type.startswith('LAYER'):
            # Extract layer number correctly (handles "LAYER2" -> "2")
            layer_num = ''.join(filter(str.isdigit, node_type))
            layers[f'LAYER{layer_num}'].append(label)

    # Update vertical positions
    layer_positions = {
        'LAYER1': gap,
        'LAYER2': gap*3,
        'LAYER3': gap*5,
        'LAYER4': gap*7,
        'LAYER5': svg_height - node_height - gap*1.5  # 600-50-75=475px
    }

    # Position nodes in their layers
    node_positions = {}
    for layer, labels in layers.items():
        if not labels:
            continue
            
        # Calculate horizontal centering
        total_width = (node_width + gap) * len(labels) - gap
        start_x = (svg_width - total_width) / 2
        
        for idx, label in enumerate(labels):
            x = start_x + (node_width + gap) * idx
            y = layer_positions[layer]
            node_positions[label] = (x, y)

    # Remove LAYER6 from styles
    layer_styles = {
        'LAYER1': {'fill': '#FFEBEE', 'stroke': '#D32F2F'},
        'LAYER2': {'fill': '#E3F2FD', 'stroke': '#2196F3', 'shape': 'rect', 'rx': '15'},
        'LAYER3': {'fill': '#F1F8E9', 'stroke': '#7CB342', 'shape': 'ellipse'},
        'LAYER4': {'fill': '#FFF3E0', 'stroke': '#EF6C00'},
        'LAYER5': {'fill': '#E8F5E9', 'stroke': '#388E3C'}
    }

    # Build SVG
    svg = f'''<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="gradient">
                <stop offset="0" stop-color="white" stop-opacity="0"/>
                <stop offset="0.4" stop-color="white" stop-opacity="1"/>
                <stop offset="0.6" stop-color="white" stop-opacity="1"/>
                <stop offset="1" stop-color="white" stop-opacity="0"/>
            </linearGradient>
            <mask id="gradient-mask">
                <rect class="mask-rect" width="200%" height="100%" fill="url(#gradient)">
                    <animate attributeName="x" 
                             from="100%" 
                             to="-100%"
                             dur="8s" 
                             repeatCount="indefinite"/>
                </rect>
            </mask>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="10" refY="3" orient="auto">
                <path d="M0,0 L0,6 L9,3 z" fill="context-stroke"/>
            </marker>
            <style>
                @keyframes dash {{
                    to {{ stroke-dashoffset: -20; }}
                }}
                .animated-line {{
                    stroke-dasharray: 5, 5;
                    animation: dash 1s linear infinite;
                }}
            </style>
        </defs>'''
    
    # Connection style configuration
    CONNECTION_STYLES = {
        '~~': {'type': 'curved', 'arrow': False, 'dashed': False, 'duration': 8},
        '~>': {'type': 'curved', 'arrow': True, 'dashed': False, 'duration': 6},
        '==': {'type': 'straight', 'arrow': False, 'dashed': False, 'duration': 6},
        '=>': {'type': 'straight', 'arrow': True, 'dashed': False, 'duration': 4},
        '--': {'type': 'dashed', 'arrow': False, 'dashed': True, 'duration': 2},
        '->': {'type': 'dashed', 'arrow': True, 'dashed': True, 'duration': 2},
        ' to ': {'type': 'solid', 'arrow': False, 'dashed': False, 'duration': 0},
        'to>': {'type': 'solid', 'arrow': True, 'dashed': False, 'duration': 0},
        '>>': {'type': 'animated', 'arrow': True, 'dashed': True, 'duration': 1}
    }
    
    # Draw connections with different animation types
    for conn in connections:
        source, target, conn_type = conn
        
        # Validate nodes exist
        source_exists = any(n[1] == source for n in nodes)
        target_exists = any(n[1] == target for n in nodes)
        if not source_exists or not target_exists:
            continue  # Skip invalid connections
        
        style = CONNECTION_STYLES.get(conn_type, CONNECTION_STYLES['>>'])
        
        # Get node types
        source_type = next(n[0] for n in nodes if n[1] == source)
        target_type = next(n[0] for n in nodes if n[1] == target)
        
        # Calculate connection points
        x1, y1 = node_positions[source]
        x2, y2 = node_positions[target]
        
        # Get node styles
        source_style = layer_styles.get(source_type, {})
        target_style = layer_styles.get(target_type, {})
        
        # Get layer numbers
        source_layer = int(''.join(filter(str.isdigit, source_type)))
        target_layer = int(''.join(filter(str.isdigit, target_type)))

        # Vertical connections
        if source_layer < target_layer:
            # Connect from bottom of source to top of target
            x1 += node_width/2
            y1 += node_height  # Bottom of source
            x2 += node_width/2
            y2 += 0  # Top of target
        else:
            # Horizontal connections
            x1 += node_width  # Right of source
            y1 += node_height/2
            x2 += 0  # Left of target
            y2 += node_height/2
        
        # Determine if connection should be animated
        is_animated = any(
            (anim_source == source and anim_target == target) or
            (anim_source == target and anim_target == source)
            for anim_source, anim_target in animations
        )
        
        # Determine animation style
        stroke_color = CONNECTION_COLORS[color_index % len(CONNECTION_COLORS)]
        color_index += 1
        
        # Create curved path
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        offset = 50
        
        # Handle curved connections: for ~~ and ~> we want a fixed upward curve
        if conn_type in ['~~', '~>']:
            if source_layer < target_layer:  # Vertical connection
                delta_y = y2 - y1
                # Use a relative factor (0.5) but enforce a minimum of 30 and maximum of 60 units offset
                offset_val = min(max(delta_y * 0.5, 30), 60)
                ctrl_x = mid_x
                ctrl_y = mid_y - offset_val
            else:
                # For horizontal or upward connections, use the fixed right/up curve
                curve_intensity = 100
                ctrl_x = mid_x + curve_intensity
                ctrl_y = mid_y - (curve_intensity * 0.6)
        else:
            # For other connection types, use the original dynamic curve
            if y1 < y2:
                ctrl_y = mid_y + offset
            else:
                ctrl_y = mid_y - offset
            ctrl_x = mid_x
        
        path_d = f"M {x1} {y1} Q {ctrl_x} {ctrl_y} {x2} {y2}"

        # Update connection rendering
        if style['type'] == 'curved':
            # Draw base layer for curved connections
            if conn_type in ['~>', '~~', '=>', '==']:
                svg += f'''
                <path d="{path_d}" 
                      stroke="rgba(238, 238, 238, 0.05)" 
                      stroke-width="2"
                      fill="none"
                      {"marker-end='url(#arrow)'" if style['arrow'] else ''}/>'''

            svg += f'''
            <path d="{path_d}" 
                  stroke="{stroke_color}" 
                  stroke-width="3"
                  fill="none"
                  {"marker-end='url(#arrow)'" if style['arrow'] else ''}
                  mask="url(#gradient-mask)">
                <animate attributeName="stroke-opacity" 
                         values="0.3;1;0.3" 
                         dur="{style['duration']}s" 
                         repeatCount="indefinite"/>
            </path>'''
        elif style['type'] == 'straight':
            # Base layer for straight connections
            if conn_type in ['=>', '==']:
                svg += f'''
                <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
                      stroke="rgba(238, 238, 238, 0.05)"
                      stroke-width="2"
                      {"marker-end='url(#arrow)'" if style['arrow'] else ''}/>'''

            svg += f'''
            <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
                  stroke="{stroke_color}"
                  stroke-width="2"
                  {"marker-end='url(#arrow)'" if style['arrow'] else ''}
                  mask="url(#gradient-mask)"/>'''
        elif style['type'] == 'dashed':
            svg += f'''
            <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
                  stroke="{stroke_color}"
                  stroke-width="2"
                  stroke-dasharray="5,5"
                  {"marker-end='url(#arrow)'" if style['arrow'] else ''}>
                <animate attributeName="stroke-dashoffset"
                         from="0" to="20"
                         dur="{style['duration']}s"
                         repeatCount="indefinite"/>
            </line>'''
        elif style['type'] == 'solid':
            svg += f'''
            <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
                  stroke="{stroke_color}"
                  stroke-width="2"
                  {"marker-end='url(#arrow)'" if style['arrow'] else ''}/>'''
        elif style['type'] == 'animated':
            svg += f'''
            <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" 
                  stroke="{stroke_color}"
                  stroke-width="2" 
                  stroke-dasharray="5,5"
                  marker-end="url(#arrow)"
                  class="animated-line"/>'''
    
    # Draw nodes
    for label, (x, y) in node_positions.items():
        layer = next(n[0] for n in nodes if n[1] == label)
        style = layer_styles.get(layer, {})
        
        if style.get('shape') == 'ellipse':
            svg += f'''
            <ellipse cx="{x + node_width/2}" cy="{y + node_height/2}" 
                     rx="{node_width/2}" ry="{node_height/2}"
                     fill="{style['fill']}" stroke="{style['stroke']}" stroke-width="3"/>'''
        else:
            rx = style.get('rx', '0')
            svg += f'''
            <rect x="{x}" y="{y}" width="{node_width}" height="{node_height}"
                  fill="{style['fill']}" stroke="{style['stroke']}" 
                  rx="{rx}" stroke-width="3"/>'''
        
        # Label
        svg += f'''
        <text x="{x + node_width/2}" y="{y + node_height/2 + 5}" 
              font-size="14" text-anchor="middle" fill="#292929">
            {label}
        </text>'''
    
    svg += "</svg>"
    
    # Wrap in HTML with styles
    return f'''
    <html>
    <body>
        <div style="width:{svg_width}px; height:{svg_height}px; border:1px solid #ccc; overflow:auto">
            {svg}
        </div>
    </body>
    </html>
    '''

if __name__ == "__main__":
    main()
