import os
import subprocess
import openai
import re
import logging
from dotenv import load_dotenv
from kubernetes import config as k8s_config
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("agent")

load_dotenv("config/config.env")

kubeconfig_path = os.getenv("KUBECONFIG", "user_kubeconfig.yaml")

def setup_kube():
    try:
        k8s_config.load_kube_config(config_file=kubeconfig_path)
        log.info(f"✅ Kubeconfig loaded from {kubeconfig_path}")
    except Exception as e:
        log.error(f"❌ Failed to load kubeconfig: {e}")
        raise

def extract_commands(text):
    raw_cmds = re.findall(r'(`?)(kubectl[^\n`]*|airctl[^\n`]*|/opt/pf9/airctl/airctl[^\n`]*)\1', text)
    commands = []
    for _, cmd in raw_cmds:
        cmd = cmd.strip()
        if cmd.startswith("/opt/pf9/airctl/airctl"):
            commands.append(cmd)
        elif cmd.startswith("airctl"):
            sub = cmd[len("airctl"):].strip()
            #if sub != "status":
            if "status" not in sub and "airctl" not in sub:
                continue  # Skip unsupported airctl subcommands
            sub = "status"
            full = f"/opt/pf9/airctl/airctl --config /opt/pf9/airctl/conf/airctl-config.yaml {sub}"
            commands.append(full)
        else:
            commands.append(cmd)
    return commands

def run_command(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True).strip()
    except subprocess.CalledProcessError as e:
        return f"❌ Command failed:\n{e.output.strip()}"

def get_ssh_ip():
    return os.getenv("SSH_IP")

def get_ssh_key_path():
    path = "/tmp/ssh_key.pem"
    if os.path.exists(path):
        return path
    return os.getenv("SSH_KEY_PATH")

def run_remote_airctl(cmd):
    log.info(f"🔗 Running remote airctl command: {cmd}")
    ip = get_ssh_ip()
    key = get_ssh_key_path()

    if not ip:
        return f"❌ Cannot run airctl: Missing SSH_IP"
    if not key:
        return f"❌ Cannot run airctl: Missing SSH_KEY_PATH"

    if os.path.exists(key):
        try:
            os.chmod(key, 0o600)
        except Exception:
            log.error(f"❌ Failed to set permissions on SSH key {key}. Ensure it is readable by the agent.")
            pass

    ssh_cmd = f'ssh -i "{key}" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@{ip} "{cmd}"'
    return run_command(ssh_cmd)

def ask_openai(prompt, system_role=None, summary_mode=False):
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    if not system_role:
        system_role = (
            "You are a Kubernetes and airctl expert.\n"
            "Convert user queries into shell commands.\n"
            "- Only return valid kubectl or airctl shell commands.\n"
            "- Never explain anything unless summarizing output."
        ) if not summary_mode else "You are a CLI expert summarizing command output."

    messages = [
        {"role": "system", "content": system_role},
        {"role": "user", "content": prompt}
    ]

    resp = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.3,
        max_tokens=3000
    )
    return resp.choices[0].message.content.strip()

def summarize_output(cmd, output, user_input):
    prompt = f"""You are a CLI expert.
User asked:
"{user_input}"

Here is the output of the command:
$ {cmd}

{output}

Explain what this means concisely."""
    return ask_openai(prompt, summary_mode=True)

def is_airctl_query(text):
    airctl_keywords = [
        "airctl status", "platform9", "controller", "cluster health", "node role", "airctl logs"
    ]
    return any(kw in text.lower() for kw in airctl_keywords)

def is_diagnostic_query(text):
    return any(x in text.lower() for x in ["why", "diagnose", "failing", "crash", "pending", "not running", "error", "stuck", "unschedulable"])

def infer_namespace_and_pod(user_input):
    prompt = f"""
You are an AI assistant helping extract Kubernetes pod name and namespace from a user question.

Extract pod name and namespace (if present) from this input:
"{user_input}"

Respond only in the format: pod=<pod-name>; namespace=<namespace or UNKNOWN>
"""
    resp = ask_openai(prompt)
    match = re.search(r"pod=([^\s;]+);\s*namespace=([^\s;]+)", resp)
    return match.groups() if match else (None, None)

def run_diagnostics(user_input):
    pod, ns = infer_namespace_and_pod(user_input)
    diag_prompt = f"""
User wants to diagnose pod status.

User asked: "{user_input}"
Pod name: {pod or 'UNKNOWN'}
Namespace: {ns or 'UNKNOWN'}

Generate the most useful kubectl commands to diagnose the pod condition.
Only output valid kubectl commands.
"""
    command_response = ask_openai(diag_prompt)
    cmds = extract_commands(command_response)
    results = []
    summaries = []

    for cmd in cmds:
        log.info(f"🧠 Running: {cmd}")
        out = run_command(cmd)
        results.append(f"$ {cmd}\n{out}")
        try:
            summaries.append(summarize_output(cmd, out, user_input))
        except Exception as e:
            summaries.append(f"⚠️ Could not summarize {cmd}:\n{e}")

    full_output = "\n\n".join(results)
    full_summary = "\n\n".join(summaries)

    return f"✅ Output:\n```\n{full_output.strip()}\n```\n\n📝 Summary:\n{full_summary.strip()}"

def process_query(user_input):
    if is_diagnostic_query(user_input):
        log.info("🔍 Diagnostic query detected. Using AI to infer commands.")
        return run_diagnostics(user_input)

    system_role = (
        "You are a Platform9 airctl expert. Return only airctl commands."
        if is_airctl_query(user_input)
        else "You are a Kubernetes expert. Return only kubectl commands."
    )

    log.info(f"🤖 Processing query: {user_input}")
    cmd_response = ask_openai(user_input, system_role)
    log.info(f"Received command response: {cmd_response}")
    cmds = extract_commands(cmd_response)

    results = []
    summaries = []

    for cmd in cmds:
        log.info(f"⚙️ Running: {cmd}")
        if cmd.strip().startswith("/opt/pf9/airctl/airctl") or cmd.strip().startswith("airctl"):
            out = run_remote_airctl(cmd)
        else:
            out = run_command(cmd)
        results.append(f"$ {cmd}\n{out}")
        if not out.startswith("❌"):
            summaries.append(summarize_output(cmd, out, user_input))

    final_output = "\n\n".join(results)
    final_summary = "\n\n".join(summaries) or "No successful command output to summarize."

    return f"✅ Output:\n```\n{final_output.strip()}\n```\n\n📝 Summary:\n{final_summary.strip()}"

def main():
    setup_kube()
    print("🤖 Agent ready! Ask your Kubernetes or airctl queries.")
    while True:
        q = input("\n💬 Ask (or type 'exit'): ").strip()
        if q.lower() in ["exit", "quit"]: break
        print(process_query(q))

if __name__ == "__main__":
    main()
