import traceback

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import COLLECTIONS_DB_URL
from app.models_init import CollectDart
from app.common.log.log_config import setup_logger
from app.config.settings import FILE_PATHS
from app.common.core.utils import get_current_datetime, make_dir


class CollectionsDatabase:
    def __init__(self) -> None:
        self.engine = create_engine(COLLECTIONS_DB_URL, pool_recycle=3600, pool_size=20, max_overflow=0)
        self.SessionLocal = sessionmaker(bind=self.engine)
        file_path = f'{FILE_PATHS["log"]}database/collections_database_{get_current_datetime()}.log'
        make_dir(file_path)
        self.logger = setup_logger(
            "collections_database",
            file_path
        )
        self.last_queried_id_collectdart = None

    def bulk_upsert_data_collectdart(self, data_list: list):
        """데이터베이스에 대량의 데이터를 저장하는 함수
        Args:
            data_list (list): 데이터 객체 리스트
        """
        session = self.SessionLocal()
        try:
            to_add = []
            for data in data_list:
                existing_data = session.query(CollectDart).filter(CollectDart.corp_code == data.corp_code).first()
                if not existing_data:
                    to_add.append(data)

            if to_add:
                session.bulk_save_objects(to_add)
                session.commit()
        except Exception as e:
            err_msg = traceback.format_exc()
            self.logger.error(f"Error: {e}\n{err_msg}")
        finally:
            session.close()

    def query_collectdart(self, batchsize=1000):
        """데이터베이스에서 데이터를 조회하는 함수
        Args:
            batchsize (int, optional): 한 번에 조회할 데이터의 개수. Defaults to 1000.
        Returns:
            list: 데이터 객체 리스트
        """
        session = self.SessionLocal()
        try:
            if self.last_queried_id_collectdart:
                existing_data = session.query(CollectDart).filter(
                    CollectDart.id > self.last_queried_id_collectdart
                    ).limit(batchsize).all()
                info_msg = f"Last queried id: {self.last_queried_id_collectdart}"
                self.logger.info(info_msg)
                print(info_msg)
            else:
                existing_data = session.query(CollectDart).limit(batchsize).all()
                info_msg = "No last queried id"
                self.logger.info(info_msg)
                print(info_msg)

            if existing_data:
                self.last_queried_id_collectdart = existing_data[-1].id
            return existing_data
        except Exception as e:
            err_msg = traceback.format_exc()
            self.logger.error(f"Error: {e}\n{err_msg}")
        finally:
            session.close()