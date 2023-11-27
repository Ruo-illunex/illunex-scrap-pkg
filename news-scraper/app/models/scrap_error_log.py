from datetime import datetime

from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import BIGINT
from pydantic import BaseModel

from app.common.db.base import BaseManager


class ScrapErrorLog(BaseManager):
    """스크래핑 에러 로그 테이블"""

    __tablename__ = 'scrap_error_log'

    error_id = Column(BIGINT, primary_key=True, autoincrement=True)
    session_log_id = Column(BIGINT, ForeignKey('scrap_session_log.log_id'))
    url = Column(Text)
    error_message = Column(Text)
    error_time = Column(DateTime)

    # 테이블 인코딩 설정
    __table_args__ = {
        'mysql_charset': 'utf8mb4',         # utf8mb4로 설정
        'mysql_collate': 'utf8mb4_unicode_ci'   # utf8mb4_unicode_ci로 설정
        }


# pydantic 모델
class ScrapErrorLogPydantic(BaseModel):
    """스크래핑 에러 로그 테이블의 Pydantic 모델"""

    error_id: int
    session_log_id: int
    url: str
    error_message: str
    error_time: datetime

    # Pydantic 모델의 Config 클래스
    class Config:
        from_attributes = True  # Pydantic 모델의 생성자의 인자로 attribute를 받을 수 있게 함
