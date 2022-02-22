class TextLog:
    def __init__(self):
        self.text = []

    def pushLine(self, text=""):
        self.text.append(text)