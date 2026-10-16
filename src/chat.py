import re
from pipeline import wrap, review_output, FAKE


class Chat:
    def __init__(self, system_prompt):
        self.history = [{"role": "system", "content": system_prompt}]
        self.tainted = False
        self.pastes = 0

    def add_paste(self, raw):
        self.pastes += 1
        rawfake = FAKE.search(raw)
        item, note = wrap(raw, f"PASTE {self.pastes}")
        banners = [note] if note else[]
        if rawfake:
            banners.append("this paste imitates a Fauve label")
        self.tainted = True
        if item is None:
            self.history.append({"role": "user", "content": "[FAUVE NOTICE] A pasted message was withheld because it could not be cleaned. Nothing from it is available."})
        else:
            self.history.append({"role": "user", "content": item })
        
        return banners

    def add_user(self, text):
        self.history.append({"role": "user", "content": text })

    def add_reply(self, raw_reply):
        text, notes = review_output(raw_reply)
        self.history.append({"role": "assistant", "content": text})
        return notes