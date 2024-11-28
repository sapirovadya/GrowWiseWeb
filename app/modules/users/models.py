from flask import Flask, jsonify
class User:
    def signup(self, data):
        user = {
            "name": data.get("name"),
            "password": data.get("password"),
        }
        return user