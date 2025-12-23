import os
import json
import requests
from typing import Dict, Any

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"
WORKSPACE = "workspace"


class EdithBrain:
    def __init__(self):
        os.makedirs(WORKSPACE, exist_ok=True)

        # ---------------- Memory ----------------
        self.memory = []
        self.max_memory = 10

        # ---------------- Delete Confirmation ----------------
        self.pending_delete = None

        # ---------------- Tool Registry ----------------
        self.tools = {
            "create_file": self._create_file,
            "delete_file": self._request_delete,
        }

        # ---------------- System Prompt ----------------
        self.system_prompt = (
            "You are EDITH, a local AI assistant.\n"
            "You remember user-provided personal details like name when stated explicitly.\n"
            "If the user asks about previously stated information, answer using memory.\n"
            "You must respond ONLY in valid JSON.\n\n"

            "Response rules:\n"
            "- Respond with EXACTLY ONE JSON object.\n"
            "- Never chain multiple actions.\n\n"

            "For chat:\n"
            "{ \"type\": \"chat\", \"content\": \"message\" }\n\n"

            "For file actions:\n"
            "{ \"type\": \"tool\", \"action\": \"create_file | delete_file\", "
            "\"args\": { \"filename\": \"example.txt\" } }\n\n"

            "Important rules:\n"
            "- Never delete files immediately.\n"
            "- Always request delete confirmation.\n"
            "- Do NOT repeat delete actions after confirmation.\n"
            "- Never include extra text."
        )

    # ---------------- Memory ----------------
    def _add_to_memory(self, role: str, content: str):
        self.memory.append({"role": role, "content": content})
        self.memory = self.memory[-self.max_memory:]

    # ---------------- Public Entry ----------------
    def process(self, user_input: str) -> str:
        # Handle delete confirmation BEFORE LLM
        if self.pending_delete:
            if user_input.lower() in ("yes", "y"):
                filename = self.pending_delete
                self.pending_delete = None
                result = self._delete_file(filename)
                self._add_to_memory("assistant", result)
                return result

            if user_input.lower() in ("no", "n"):
                self.pending_delete = None
                result = "❌ Delete cancelled."
                self._add_to_memory("assistant", result)
                return result

            return "⚠️ Please confirm delete: yes or no."

        # Call LLM
        raw_response = self._ask_llm(user_input)
        parsed = self._parse_response(raw_response)

        if not parsed:
            return "⚠️ Invalid AI response."

        if parsed["type"] == "chat":
            self._add_to_memory("assistant", parsed["content"])
            return parsed["content"]

        if parsed["type"] == "tool":
            result = self._execute_tool(parsed)
            self._add_to_memory("assistant", result)
            return result

        return "⚠️ Unknown response type."

    # ---------------- LLM ----------------
    def _ask_llm(self, user_input: str) -> str:
        self._add_to_memory("user", user_input)

        history = ""
        for msg in self.memory:
            history += f"{msg['role'].capitalize()}: {msg['content']}\n"

        prompt = f"{self.system_prompt}\n\n{history}Assistant:"

        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        return response.json()["response"].strip()

    # ---------------- Parser ----------------
    def _parse_response(self, text: str) -> Dict[str, Any] | None:
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Fallback: extract outermost JSON
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end + 1])
        except Exception:
            pass

        print("RAW LLM RESPONSE (unparseable):", text)
        return None

    # ---------------- Tool Executor ----------------
    def _execute_tool(self, data: Dict[str, Any]) -> str:
        action = data.get("action")
        args = data.get("args", {})

        tool = self.tools.get(action)
        if not tool:
            return "⚠️ Unknown tool."

        return tool(args.get("filename"))

    # ---------------- File Tools ----------------
    def _create_file(self, filename: str | None) -> str:
        if not filename:
            return "❌ Filename missing."

        path = os.path.join(WORKSPACE, os.path.basename(filename))
        if os.path.exists(path):
            return f"❌ File already exists: {filename}"

        with open(path, "w"):
            pass

        return f"✅ File created: {filename}"

    def _delete_file(self, filename: str | None) -> str:
        if not filename:
            return "❌ Filename missing."

        path = os.path.join(WORKSPACE, os.path.basename(filename))
        if not os.path.exists(path):
            return f"❌ File not found: {filename}"

        os.remove(path)
        return f"🗑️ File deleted: {filename}"

    # ---------------- Delete Request ----------------
    def _request_delete(self, filename: str | None) -> str:
        if not filename:
            return "❌ Filename missing."

        self.pending_delete = filename
        return f"⚠️ Are you sure you want to delete '{filename}'? (yes/no)"
