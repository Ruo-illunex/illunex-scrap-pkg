import traceback

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import NEWS_DB_URL
from app.models_init import DaumNews, NaverNews, EtcNews, EsgNews


class NewsDatabase:
    def __init__(self):
        self.engine = create_engine(NEWS_DB_URL, pool_recycle=3600, pool_size=20, max_overflow=0)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.existing_data = None

    # 뉴스 데이터베이스에 대량의 데이터를 저장하는 함수
    def save_data_bulk(self, news_data_list: list, portal: str):
        """뉴스 데이터베이스에 데이터를 대량으로 저장하는 함수
        Args:
            news_data_list (list): 뉴스 데이터 객체 리스트
            portal (str): 포털 이름
        """
        session = self.SessionLocal()
        try:
            to_add = []
            for news_data in news_data_list:
                existing_data = None
                # 기존 데이터 확인 로직 (기존 로직을 사용)
                if portal == "naver":
                    existing_data = session.query(NaverNews).filter(NaverNews.url_md5 == news_data.url_md5).first()
                elif portal == "daum":
                    existing_data = session.query(DaumNews).filter(DaumNews.url_md5 == news_data.url_md5).first()
                elif portal in ['venturesquare', 'zdnet', 'the bell', 'startuptoday', 'startupn', 'platum']:
                    existing_data = session.query(EtcNews).filter(EtcNews.url_md5 == news_data.url_md5).first()
                elif portal in ['esg_economy', 'greenpost_korea']:
                    existing_data = session.query(EsgNews).filter(EsgNews.url_md5 == news_data.url_md5).first()

                # 기존 데이터가 없으면 to_add 리스트에 추가
                if not existing_data:
                    to_add.append(news_data)

            # to_add에 있는 모든 뉴스 데이터를 한 번에 데이터베이스에 저장
            if to_add:
                session.bulk_save_objects(to_add)
                session.commit()
        except Exception as e:
            stack_trace = traceback.format_exc()
            print(f"Error: {e}\n{stack_trace}")
        finally:
            session.close()
