import os
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"

WORKSPACE = "workspace"


class EdithBrain:
    def __init__(self):
        os.makedirs(WORKSPACE, exist_ok=True)

        self.system_prompt = (
            "You are EDITH, a local AI assistant.\n"
            "You can chat normally.\n"
            "If the user asks to create or delete a file, "
            "respond with one of these commands ONLY:\n\n"
            "CREATE_FILE:<filename>\n"
            "DELETE_FILE:<filename>\n\n"
            "Otherwise, respond normally in plain text."
        )

        self.memory = []

    # ---------- public method ----------
    def process(self, user_input: str) -> str:
        response = self._ask_llm(user_input)

        # handle file commands
        if response.startswith("CREATE_FILE:"):
            filename = response.replace("CREATE_FILE:", "").strip()
            return self._create_file(filename)

        if response.startswith("DELETE_FILE:"):
            filename = response.replace("DELETE_FILE:", "").strip()
            return self._delete_file(filename)

        return response

    # ---------- internal methods ----------
    def _ask_llm(self, user_input: str) -> str:
        prompt = self.system_prompt + "\n\nUser: " + user_input + "\nAssistant:"

        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        return response.json()["response"].strip()

    def _create_file(self, filename: str) -> str:
        path = os.path.join(WORKSPACE, os.path.basename(filename))
        with open(path, "w") as f:
            f.write("")
        return f"✅ File created: {filename}"

    def _delete_file(self, filename: str) -> str:
        path = os.path.join(WORKSPACE, os.path.basename(filename))
        if not os.path.exists(path):
            return f"❌ File not found: {filename}"

        os.remove(path)
        return f"🗑️ File deleted: {filename}"