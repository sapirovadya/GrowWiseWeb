from modules.users.models import User

class Job_Seeker(User):
    def signup(self, data):
        job_seeker = super().signup(data)  # קריאה למתודת `signup` של המחלקה `User`
        job_seeker["is_approved"] = 1  # כל מנהל מאושר אוטומטית
        return job_seeker
