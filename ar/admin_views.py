from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.principal import Permission, RoleNeed

admin_permission = Permission(RoleNeed('admin'))


class BaseModelView(ModelView):
    def is_accessible(self):
        return admin_permission.can()
    column_display_pk = True


class SubredditModelView(BaseModelView):
    form_columns = ("name", )
