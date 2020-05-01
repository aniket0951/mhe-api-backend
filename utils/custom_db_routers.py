class CustomDBRouter:
    def db_for_read(self, model, **hints):
        return 'read_db'

    def db_for_write(self, model, **hints):
        return 'write_db'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if both objects are
        in the primary/replica pool.
        """
        db_list = ('default', 'read_db', 'write_db')
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        All non-auth models end up in this pool.
        """
        return True
