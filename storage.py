class Message:
    def __init__(self, sender_id, sender_name, text, chat_id):
        self.sender_id = sender_id  # ID отправителя
        self.sender_name = sender_name  # Имя отправителя
        self.text = text  # Текст сообщения
        self.chat_id = chat_id  # ID чата

class MessageStorage:
    def __init__(self):
        self.messages = []  # Список сообщений
        self._custom_names = {}  # Пользовательские имена
        self._rename_states = {}  # Состояния переименования

    def add_message(self, message):
        self.messages.append(message)  # Добавить сообщение

    def clear(self):
        self.messages.clear()  # Очистить всё

    # ... остальные методы (пока не важно)
