from modules.users.models import User

class Co_Manager(User):
    def signup(self, data):
        co_manager = super().signup(data)  # קריאה למתודת `signup` של המחלקה `User`
        co_manager["is_approved"] = 0  # כל מנהל מאושר אוטומטית
        co_manager["manager_email"] = data.get("manager_email")

        return co_manager