from modules.users.models import User

class Manager(User):
    def signup(self, data):
        manager = super().signup(data)  # קריאה למתודת `signup` של המחלקה `User`
        manager["is_approved"] = 1  # כל מנהל מאושר אוטומטית
        manager["location"] = data.get("location")
        return manager
