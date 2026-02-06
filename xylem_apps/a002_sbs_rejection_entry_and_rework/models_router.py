class A002Router:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'a002_sbs_rejection_entry_and_rework':
            return 'a002_sbs_rejection_entry_and_rework'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'a002_sbs_rejection_entry_and_rework':
            return 'a002_sbs_rejection_entry_and_rework'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'a002_sbs_rejection_entry_and_rework' or \
           obj2._meta.app_label == 'a002_sbs_rejection_entry_and_rework':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'a002_sbs_rejection_entry_and_rework':
            return db == 'a002_sbs_rejection_entry_and_rework'
        return None