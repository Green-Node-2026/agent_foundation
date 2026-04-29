from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add parent directory to path to import main and calculator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import agent_loop

app = Flask(__name__)
CORS(app)

def serialize_content(contents):
    serialized = []
    for content in contents:
        parts = []
        for part in content.parts:
            p = {}
            if part.text:
                p["text"] = part.text
            if part.function_call:
                p["function_call"] = {
                    "name": part.function_call.name,
                    "args": part.function_call.args
                }
            if part.function_response:
                p["function_response"] = {
                    "name": part.function_response.name,
                    "response": part.function_response.response
                }
            parts.append(p)
        serialized.append({
            "role": content.role,
            "parts": parts
        })
    return serialized

import traceback

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    
    try:
        history = agent_loop(prompt)
        return jsonify({"history": serialize_content(history)})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
