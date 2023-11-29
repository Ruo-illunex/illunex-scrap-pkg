from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.mysql import BIGINT
from pydantic import BaseModel

from app.common.db.base import BaseScraper


class EsgNews(BaseScraper):
    """ESG 뉴스 모델 클래스"""

    __tablename__ = 'esg_news'

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    url = Column(String(255))
    title = Column(String(255))
    content = Column(Text)
    create_date = Column(DateTime)
    kind = Column(String(10))
    #url_md5는 unique key로 설정
    url_md5 = Column(String(35))
    image_url = Column(Text)
    portal = Column(String(255))
    media = Column(String(255))
    category = Column(String(255))
    esg_analysis = Column(Text)

    # 테이블 인코딩 설정
    __table_args__ = {
        'mysql_charset': 'utf8mb4',         # utf8mb4로 설정
        'mysql_collate': 'utf8mb4_unicode_ci'   # utf8mb4_unicode_ci로 설정
        }


class EsgNewsPydantic(BaseModel):
    """ESG 뉴스 모델 클래스의 Pydantic 모델"""

    url: str
    title: str
    content: str
    create_date: datetime
    kind: str
    url_md5: str
    image_url: str
    portal: str
    media: str
    category: str
    esg_analysis: str

    # Pydantic 모델의 Config 클래스
    class Config:
        from_attributes = True  # Pydantic 모델의 생성자의 인자로 attribute를 받을 수 있게 함
