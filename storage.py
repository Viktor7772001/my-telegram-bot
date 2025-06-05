class Message:
    def __init__(self, sender_id, sender_name, text, chat_id):
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.text = text
        self.chat_id = chat_id

class MessageStorage:
    def __init__(self):
        self.messages = []
        self._custom_names = {}
        self._rename_states = {}

    def add_message(self, message):
        self.messages.append(message)

    def clear(self):
        self.messages.clear()

    def set_custom_name(self, user_id, name):
        """Assign a custom name to a user."""
        self._custom_names[user_id] = name

    def get_name(self, user_id, fallback):
        """Return custom name for user if set, otherwise fallback."""
        return self._custom_names.get(user_id, fallback)

    def start_renaming(self, admin_id):
        """Prepare renaming state for the admin. Returns first user id or None."""
        unique_ids = []
        seen = set()
        for msg in self.messages:
            if msg.sender_id not in seen:
                unique_ids.append(msg.sender_id)
                seen.add(msg.sender_id)
        if not unique_ids:
            return None
        self._rename_states[admin_id] = {"ids": unique_ids, "index": 0}
        return unique_ids[0]

    def record_name(self, admin_id, name):
        state = self._rename_states.get(admin_id)
        if not state:
            return None
        current_id = state["ids"][state["index"]]
        self.set_custom_name(current_id, name)
        return self.next_rename(admin_id)

    def next_rename(self, admin_id):
        state = self._rename_states.get(admin_id)
        if not state:
            return None
        state["index"] += 1
        if state["index"] >= len(state["ids"]):
            self._rename_states.pop(admin_id, None)
            return None
        return state["ids"][state["index"]]

    def is_renaming(self, admin_id):
        return admin_id in self._rename_states
