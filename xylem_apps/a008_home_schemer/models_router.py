class A008Router:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'a008_home_schemer':
            return 'a008_home_schemer'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'a008_home_schemer':
            return 'a008_home_schemer'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'a008_home_schemer' or \
           obj2._meta.app_label == 'a008_home_schemer':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'a008_home_schemer':
            return db == 'a008_home_schemer'
        return None