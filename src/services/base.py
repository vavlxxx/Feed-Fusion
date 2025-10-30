from utils.db_tools import DBManager


class BaseService:
    def __init__(self, db_manager: DBManager | None) -> None:
        if db_manager is not None:
            self.db = db_manager
