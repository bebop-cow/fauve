DAY = 86400

class Retention:
    def __init__(self, clock, items=None):
        self.clock = clock
        self.items = items if items is not None else {}   # key -> time saved
        self.kept = set()

    def add(self, key):
         self.items[key] = self.clock()

    def age_days(self, key):
        return (self.clock() - self.items[key]) / DAY

    def prompts_due(self):
        keys_for_prompts = []
        for key in self.items:
            prompt_day, erase_day = self._limits(key)
            if prompt_day <= self.age_days(key) < erase_day:
                keys_for_prompts.append(key)
        return keys_for_prompts          

    def sweep(self):
        # remove every key at least 7 days old, return the removed keys
        keys_to_remove =[]
        for key in list(self.items):
            _, erase_day = self._limits(key)
            if self.age_days(key) >= erase_day:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self.items.pop(key)
            self.kept.discard(key)

        return keys_to_remove

    def launch(self):
        # what the app does at startup (one line)
        return self.sweep()

    def _limits(self, key):
        # return (prompt_day, erase_day) for this key
        if key in self.kept:
            return (14, 18)
        else:
            return (3, 7)

    def keep(self, key):
        # only if the item exists: reset its time, mark it kept
        keep_list = []
        if key in self.items:
            self.items[key] = self.clock()
            self.kept.add(key)


