class A001Router:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'a001_qa_report_and_reprocess':
            return 'a001_qa_report_and_reprocess'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'a001_qa_report_and_reprocess':
            return 'a001_qa_report_and_reprocess'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'a001_qa_report_and_reprocess' or \
           obj2._meta.app_label == 'a001_qa_report_and_reprocess':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'a001_qa_report_and_reprocess':
            return db == 'a001_qa_report_and_reprocess'
        return None