# GenAI-AWS-Diagram-Animator

GenAI-AWS-Diagram-Animator is an interactive application that generates animated AWS architecture diagrams based on a simple text specification. Built with Streamlit and Graphviz—and with optional AWS integration—this tool helps you quickly visualize and animate cloud architecture designs.

## Overview

The GenAI-AWS-Diagram-Animator allows users to define diagram nodes and connections using a plain-text format. The tool parses these inputs, calculates node positions and connection paths (including curved, dashed, and animated lines), and then generates an SVG diagram with smooth animations. It is useful for:
- Prototyping AWS architectural diagrams.
- Demonstrating dynamic relationships between services.
- Sharing visual designs with your team.

## Features

- **Text-Based Input:** Define nodes and connections (using connectors like `~>`, `to>`, `>>`, etc.) with a simple format.
- **Custom Animations:** Animated connections leverage SVG masks and CSS animations for a flowing visual effect.
- **Interactive Diagram Generation:** Built with Streamlit for an intuitive web UI.
- **Downloadable Output:** Generate an SVG diagram that can be viewed in the browser or downloaded.
- **AWS Integration (Optional):** Optionally invoke AWS Bedrock models through boto3 for GenAI services.

## Installation

### Prerequisites

- Python 3.7 or above.
- AWS credentials configured (if using AWS Bedrock features).
- Graphviz (required for diagram generation).

### Dependencies

Install the required Python packages with pip:
