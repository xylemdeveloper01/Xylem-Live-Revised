class A009Router:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'a009_building_management_system':
            return 'a009_building_management_system'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'a009_building_management_system':
            return 'a009_building_management_system'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'a009_building_management_system' or \
           obj2._meta.app_label == 'a009_building_management_system':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'a009_building_management_system':
            return db == 'a009_building_management_system'
        return None