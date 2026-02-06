class A000Router:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'a000_xylem_master':
            return 'default'
        if model._meta.app_label == 'django_cache' and model._meta.model_name == 'cacheentry':
            return 'cache_db'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'a000_xylem_master':
            return 'default'
        if model._meta.app_label == 'django_cache' and model._meta.model_name == 'cacheentry':
            return 'cache_db'
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'a000_xylem_master' or \
           obj2._meta.app_label == 'a000_xylem_master':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        defalut_app_list = ['admin', 'auth', 'contenttypes', 'sessions', 'a000_xylem_master']
        if app_label == 'django_cache' and model_name == 'cacheentry':
            return db == 'cache_db'
        if app_label in defalut_app_list:
            return db == 'default'
        
        return None