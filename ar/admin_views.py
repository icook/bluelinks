from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.principal import Permission, RoleNeed
from flask.ext.security import SQLAlchemyUserDatastore

import wtforms as field

from .models import Community

admin_permission = Permission(RoleNeed('admin'))


class BaseModelView(ModelView):
    def is_accessible(self):
        return admin_permission.can()
    column_display_pk = True


class CommunityModelView(BaseModelView):
    form_columns = ("name", )


class PostModelView(BaseModelView):
    form_overrides = dict(text=field.TextAreaField)


class SQLAlchemyUserDatastoreCustom(SQLAlchemyUserDatastore):
    def create_user(self, **kwargs):
        user = super().create_user(**kwargs)
        comm_list = ["pics", "funny", "videos", "news", "science", "meta"]
        comms = Community.query.filter(Community.name.in_(comm_list))
        for com in comms:
            user.subscriptions.append(com)
        return user
