class A006Router:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'a006_4m_digitalization':
            return 'a006_4m_digitalization'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'a006_4m_digitalization':
            return 'a006_4m_digitalization'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'a006_4m_digitalization' or \
           obj2._meta.app_label == 'a006_4m_digitalization':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'a006_4m_digitalization':
            return db == 'a006_4m_digitalization'
        return None