class CustomDBRouter:
    def db_for_read(self, model, **hints):
        return 'read_db'

    def db_for_write(self, model, **hints):
        return 'write_db'