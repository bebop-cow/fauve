DAY = 86400

class Retention:
    def __init__(self, clock, items=None):
        self.clock = clock
        self.items = items if items is not None else {}   # key -> time saved

    def add(self, key):
         self.items[key] = self.clock()

    def age_days(self, key):
        return (self.clock() - self.items[key]) / DAY

    def prompts_due(self):
        keys_for_prompts = []
        for key in self.items:
            if 3 <= self.age_days(key) < 7:
                keys_for_prompts.append(key)
        return keys_for_prompts          
        

    def sweep(self):
        # remove every key at least 7 days old, return the removed keys
        keys_to_remove =[]
        for key in list(self.items):
            if self.age_days(key) >= 7:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self.items.pop(key)

        return keys_to_remove

    def launch(self):
        # what the app does at startup (one line)
        return self.sweep()