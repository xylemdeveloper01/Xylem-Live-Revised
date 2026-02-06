class A003Router:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'a003_smart_alerts':
            return 'a003_smart_alerts'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'a003_smart_alerts':
            return 'a003_smart_alerts'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'a003_smart_alerts' or \
           obj2._meta.app_label == 'a003_smart_alerts':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'a003_smart_alerts':
            return db == 'a003_smart_alerts'
        return None