from pipeline import wrap

class Chat:
    def __init__(self, system_prompt):
        self.history = [{"role": "system", "content": system_prompt}]
        self.tainted = False
        self.pastes = 0

    def add_paste(self, raw):
        self.pastes += 1
        item, note = wrap(raw, f"PASTE {self.pastes}")
        banners = [note] if note else[]
        self.tainted = True
        if item is None:
            self.history.append({"role": "user", "content": "[FAUVE NOTICE] A pasted message was withheld because it could not be cleaned. Nothing from it is available."})
        else:
            self.history.append({"role": "user", "content": item })
        

        return banners

    def add_user(self, text):
        self.history.append({"role": "user", "content": text })
        