from flask import Flask, request, jsonify, render_template
from agent.core import process_query
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        user_input = data.get("query", "")
        log.info(f"Received query: {user_input}")
        response = process_query(user_input)
        return jsonify({"response": response})
    except Exception as e:
        log.exception("❌ Error during query processing")
        return jsonify({"response": f"Internal server error: {str(e)}"}), 500

@app.route("/set-kubeconfig", methods=["POST"])
def set_kubeconfig():
    try:
        data = request.get_json()
        raw_config = data.get("kubeconfig", "").strip()
        if not raw_config:
            return jsonify({"message": "❌ Kubeconfig is empty."}), 400

        kube_path = os.path.abspath("user_kubeconfig.yaml")
        with open(kube_path, "w") as f:
            f.write(raw_config)

        os.environ["KUBECONFIG"] = kube_path
        log.info(f"✅ Kubeconfig updated via UI and saved at {kube_path}")

        return jsonify({"message": "✅ Kubeconfig successfully saved."})
    except Exception as e:
        log.exception("❌ Failed to save kubeconfig")
        return jsonify({"message": f"❌ Error saving kubeconfig: {str(e)}"}), 500

@app.route("/set-ssh-ip", methods=["POST"])
def set_ssh_ip():
    try:
        data = request.get_json()
        ssh_ip = data.get("ssh_ip", "").strip()

        if not ssh_ip:
            return jsonify({"message": "❌ SSH IP is empty."}), 400

        os.environ["SSH_IP"] = ssh_ip
        log.info(f"✅ SSH IP saved: {ssh_ip}")

        return jsonify({"message": "✅ SSH IP successfully saved."})
    except Exception as e:
        log.exception("❌ Failed to save SSH IP")
        return jsonify({"message": f"❌ Error saving SSH IP: {str(e)}"}), 500

@app.route("/set-ssh-key", methods=["POST"])
def set_ssh_key():
    try:
        data = request.get_json()
        ssh_key = data.get("ssh_key", "").strip()

        if not ssh_key:
            return jsonify({"message": "❌ SSH key is empty."}), 400

        key_path = os.path.abspath("ssh_key.pem")
        with open(key_path, "w") as f:
            f.write(ssh_key)

        # Fix file permissions to 600
        os.chmod(key_path, 0o600)
        log.info(f"✅ SSH key saved to {key_path} with permissions 0600")

        os.environ["SSH_KEY_PATH"] = key_path
        return jsonify({"message": "✅ SSH key successfully saved."})
    except Exception as e:
        log.exception("❌ Failed to save SSH key")
        return jsonify({"message": f"❌ Error saving SSH key: {str(e)}"}), 500

@app.route("/set-openai-key", methods=["POST"])
def set_openai_key():
    data = request.get_json()
    api_key = data.get("api_key", "").strip()

    if not api_key.startswith("sk-"):
        return jsonify({"message": "❌ Invalid API key format."}), 400

    os.environ["OPENAI_API_KEY"] = api_key
    log.info(f"🔐 Received new OpenAI API key")
    return jsonify({"message": "✅ OpenAI API key saved."})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
