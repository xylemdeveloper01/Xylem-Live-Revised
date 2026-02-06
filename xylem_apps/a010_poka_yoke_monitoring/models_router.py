class A010Router:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'a010_poka_yoke_monitoring':
            return 'a010_poka_yoke_monitoring'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'a010_poka_yoke_monitoring':
            return 'a010_poka_yoke_monitoring'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'a010_poka_yoke_monitoring' or \
           obj2._meta.app_label == 'a010_poka_yoke_monitoring':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'a010_poka_yoke_monitoring':
            return db == 'a010_poka_yoke_monitoring'
        return None