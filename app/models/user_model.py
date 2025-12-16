
class UserModel:
    users = [
        {"id": 1, "name": "João"},
        {"id": 2, "name": "Maria"}
    ]
    next_id = 3

    @classmethod
    def get_all_users(cls):
        return cls.users

    @classmethod
    def create_user(cls, name):
        user = {"id": cls.next_id, "name": name}
        cls.next_id += 1
        cls.users.append(user)
        return user

    @classmethod
    def update_user(cls, user_id, name):
        for user in cls.users:
            if user["id"] == user_id:
                user["name"] = name
                return user
        return None

    @classmethod
    def delete_user(cls, user_id):
        for user in cls.users:
            if user["id"] == user_id:
                cls.users.remove(user)
                return True
        return False
