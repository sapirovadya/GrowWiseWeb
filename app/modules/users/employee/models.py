from modules.users.models import User

class Employee(User):
    def signup(self, data):
        employee = super().signup(data)  # קריאה למתודת `signup` של המחלקה `User`
        employee["is_approved"] = 0  # עובד חדש אינו מאושר כברירת מחדל
        employee["manager_email"] = data.get("manager_email")
        return employee
