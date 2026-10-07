import time

CART_TOOLS = {"add_to_cart", "view_cart", "update_cart"}

class Session:
    def __init__(self, ttl, clock=time.time):
        self.clock = clock
        self.expires_at = self.clock() + ttl
        self.cookies = {}

    def alive(self):
        if self.clock() >= self.expires_at:
            self.cookies.clear()
            return False
        return True

    def call_tool(self, name):
        if name in CART_TOOLS and not self.alive():
            return "refused: session expired"
        return "ok"