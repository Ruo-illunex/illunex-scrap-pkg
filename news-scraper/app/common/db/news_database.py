import traceback

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import NEWS_DB_URL
from app.models_init import DaumNews, NaverNews, EtcNews


class NewsDatabase:
    def __init__(self):
        self.engine = create_engine(NEWS_DB_URL, pool_recycle=3600, pool_size=20, max_overflow=0)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.existing_data = None


    # 뉴스 데이터베이스에 데이터를 저장하는 함수
    def save_news_data(self, news_data, portal: str):
        """뉴스 데이터베이스에 데이터를 저장하는 함수
        Args:
            news_data (NaverNews or DaumNews or EtcNews): 뉴스 데이터
            portal (str): 포털 이름
        """

        # 뉴스 데이터베이스 세션 생성
        session = self.SessionLocal()

        try:
            # 'url_md5' 필드를 이용해 기존 데이터가 있는지 확인
            if portal == "naver":
                self.existing_data = session.query(NaverNews).filter(NaverNews.url_md5 == news_data.url_md5).first()
            elif portal == "daum":
                self.existing_data = session.query(DaumNews).filter(DaumNews.url_md5 == news_data.url_md5).first()
            elif portal == "etc":
                self.existing_data = session.query(EtcNews).filter(EtcNews.url_md5 == news_data.url_md5).first()

            # 기존 데이터가 없을 경우에만 새 데이터 추가
            if not self.existing_data:
                session.add(news_data)
                session.commit()
        except Exception as e:
            stack_trace = traceback.format_exc()
            print(f"Error: {e}\n{stack_trace}")
        finally:
            # 세션 닫기
            session.close()
