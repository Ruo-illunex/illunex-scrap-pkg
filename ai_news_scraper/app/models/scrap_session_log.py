from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.mysql import BIGINT
from pydantic import BaseModel

from app.common.db.base import BaseManager


class ScrapSessionLog(BaseManager):
    """스크래핑 세션 로그 테이블"""

    __tablename__ = 'scrap_session_log'

    log_id = Column(BIGINT, primary_key=True, autoincrement=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    total_records_processed = Column(Integer)
    success_count = Column(Integer)
    fail_count = Column(Integer)
    remarks = Column(Text)

    # 테이블 인코딩 설정
    __table_args__ = {
        'mysql_charset': 'utf8mb4',         # utf8mb4로 설정
        'mysql_collate': 'utf8mb4_unicode_ci'   # utf8mb4_unicode_ci로 설정
        }


# pydantic 모델
class ScrapSessionLogPydantic(BaseModel):
    """스크래핑 세션 로그 테이블의 Pydantic 모델"""

    log_id: int
    start_time: datetime
    end_time: datetime
    total_records_processed: int
    success_count: int
    fail_count: int
    remarks: str

    # Pydantic 모델의 Config 클래스
    class Config:
        from_attributes = True  # Pydantic 모델의 생성자의 인자로 attribute를 받을 수 있게 함
