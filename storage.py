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
