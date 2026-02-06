class A005Router:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'a005_qa_patrol_check':
            return 'a005_qa_patrol_check'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'a005_qa_patrol_check':
            return 'a005_qa_patrol_check'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'a005_qa_patrol_check' or \
           obj2._meta.app_label == 'a005_qa_patrol_check':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'a005_qa_patrol_check':
            return db == 'a005_qa_patrol_check'
        return None