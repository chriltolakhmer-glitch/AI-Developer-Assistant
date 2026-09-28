class DatabaseClient:
    def connect(self, dsn):
        return {"dsn": dsn, "connected": True}


def connect_database(dsn):
    return DatabaseClient().connect(dsn)
