# PCD Cluster Assistant

PCD Cluster Assistant is a smart AI-powered CLI assistant that helps diagnose Kubernetes issues and query Platform9 clusters using kubectl and airctl. It uses OpenAI's API to semantically interpret user queries and convert them into precise CLI commands — ideal for debugging pods or checking cluster health.

## Features

- AI-driven command generation using OpenAI
- Diagnose Kubernetes pods stuck in Pending, CrashLoopBackOff, etc.
- Remote airctl access over SSH to Platform9 clusters
- Smart summaries of command output
- Simple Flask-based Web UI

## Setup

### 1. Clone and Setup Virtual Environment

git clone git@github.com:deepaksahu-pf9/pcd-agent.git
cd pcd-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

### 2. Configure .env (optional)

Edit `config/config.env` to set static fallback config:

OPENAI_API_KEY=sk-xxxxx

KUBECONFIG=/absolute/path/to/kubeconfig.yaml

SSH_IP=remote-ip

SSH_KEY_PATH=/absolute/path/to/ssh_key.pem

Note: You can also upload these directly via the UI per session — no need to hardcode.

## Running the Agent: Can run either in CLI or UI mode

### CLI Mode

python -m agent.core

### Web UI Mode

python web.py

Then open your browser at: http://localhost:5000 or http://host-ip:5000

From here, you can:
- Enter natural language queries like “Why is pod X pending?”
- Upload OpenAI key, SSH key, kubeconfig, and SSH IP via the form
- View generated commands and their summaries