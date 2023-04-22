import time

class GuestList:
    def __init__(self):
        self.guests = {}

    def add_guest(self, name, expiration_time):
        self.guests[name] = expiration_time

    def remove_expired_guests(self):
        current_time = time.time()
        self.guests = {k: v for k, v in self.guests.items() if v > current_time}

    def get_guests(self):
        self.remove_expired_guests()
        return list(self.guests.keys())

guest_list = GuestList()
