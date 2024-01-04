import traceback
from collections import defaultdict

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

from app.config.settings import SCRAPER_MNG_DB_URL
from app.models.scrap_session_log import ScrapSessionLog


class ScraperManagerDatabase:
    def __init__(self):
        self.engine = create_engine(SCRAPER_MNG_DB_URL, pool_recycle=3600, pool_size=20, max_overflow=0)
        self.SessionLocal = sessionmaker(bind=self.engine)


    # scraper_mng 세션을 반환하는 함수
    def get_session_scraper_mng(self):
        """scraper_mng 세션을 반환하는 함수"""

        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()


    # scrap_session_log 테이블에 데이터를 저장하는 함수
    def save_scrap_session_log(self, session_log):
        """scrap_session_log 테이블에 데이터를 저장하는 함수
        Args:
            session_log (dict): 세션 로그
        Returns:
            int: 세션 로그 id
        """

        # 세션 로그 데이터베이스 세션 생성
        session = self.SessionLocal()

        try:
            # 데이터를 저장하고 해당 데이터의 id를 반환
            session.add(session_log)
            session.commit()
            session.refresh(session_log)
            return session_log.log_id
        except Exception as e:
            stack_trace = traceback.format_exc()
            print(f"Error: {e}\n{stack_trace}")
            return None
        finally:
            session.close()

    # scrap_error_log 테이블에 데이터를 저장하는 함수
    def save_scrap_error_logs(self, error_logs):
        """scrap_error_log 테이블에 데이터를 저장하는 함수
        Args:
            error_logs (list): 에러 로그 리스트
        """

        # 에러 로그 데이터베이스 세션 생성
        session = self.SessionLocal()

        try:
            # 여러 에러 로그 객체를 세션에 한 번에 추가
            session.add_all(error_logs)
            session.commit()
        except Exception as e:
            stack_trace = traceback.format_exc()
            print(f"Error: {e}\n{stack_trace}")
        finally:
            session.close()

    def get_scraping_statistics_by_portal(self, date):
        """특정 날짜에 대한 포털별 스크래핑 통계를 가져오는 함수
        Args:
            date (datetime.date): 조회할 날짜
        Returns:
            dict: 포털별 스크래핑 통계
        """

        # 세션 열기
        session = self.SessionLocal()

        try:
            # 해당 날짜의 스크래핑 로그를 포털별로 그룹화하여 조회
            results = session.query(
                ScrapSessionLog.remarks,
                func.sum(ScrapSessionLog.success_count),
                func.sum(ScrapSessionLog.fail_count)
            ).filter(
                func.date(ScrapSessionLog.start_time) == date
            ).group_by(
                ScrapSessionLog.remarks
            ).all()

            # 결과를 딕셔너리로 변환
            portal_stats = defaultdict(dict)
            for remark, success_count, fail_count in results:
                portal_stats[remark]['success'] = success_count
                portal_stats[remark]['fail'] = fail_count

            return portal_stats
        finally:
            # 세션 닫기
            session.close()
