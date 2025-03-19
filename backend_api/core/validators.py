import re
from rest_framework import serializers


def validate_strong_password(password):
    if len(password) < 8:
        raise serializers.ValidationError({"code": 1003})  # Le mot de passe doit contenir au moins 8 caractères.
    if not any(char.isdigit() for char in password):
        raise serializers.ValidationError({"code": 1004})  # Le mot de passe doit contenir au moins un chiffre.
    if not any(char.islower() for char in password):
        raise serializers.ValidationError({"code": 1005})  # Le mot de passe doit contenir au moins une lettre minuscule.
    if not any(char.isupper() for char in password):
        raise serializers.ValidationError({"code": 1006})  # Le mot de passe doit contenir au moins une lettre majuscule.
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise serializers.ValidationError({"code": 1007})  # Le mot de passe doit contenir au moins un caractère spécial.
