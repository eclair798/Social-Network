from flask_marshmallow import Marshmallow
ma = Marshmallow()

class UserSchema(ma.Schema):
    class Meta:
        fields = ('user_id', 'username', 'email', 'created_at', 'updated_at')

user_schema = UserSchema()
users_schema = UserSchema(many=True)
