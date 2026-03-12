from django.urls import reverse
from ninja import ModelSchema

from fca.users.models import User


class UpdateUserSchema(ModelSchema):
    class Meta:
        model = User
        fields = ["username", "name"]


class UserSchema(ModelSchema):
    url: str

    class Meta:
        model = User
        fields = ["username", "email", "name"]

    @staticmethod
    def resolve_url(obj: User):
        return reverse("api:retrieve_user", kwargs={"username": obj.username})
