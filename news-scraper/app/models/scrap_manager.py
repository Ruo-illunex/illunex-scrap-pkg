from typing import Dict, Any
from pydantic import BaseModel
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.common.db.base import BaseManager


class ScrapManager(BaseManager):
    """스크래핑 매니저 모델 클래스"""

    __tablename__ = 'scrap_manager'

    id = Column(Integer, primary_key=True, autoincrement=True)
    portal = Column(String(255), nullable=False)
    parsing_target_name = Column(String(255), nullable=False)
    parsing_method = Column(String(255), nullable=False)
    parsing_rule = Column(JSON, nullable=False)
    created = Column(DateTime, default=func.current_timestamp())
    updated = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


class ScrapManagerPydantic(BaseModel):
    """스크래핑 매니저 모델 클래스의 Pydantic 모델"""

    portal: str
    parsing_target_name: str
    parsing_method: str
    # 키는 str 타입, 값은 str 또는 dict 타입인 dict
    parsing_rule: Dict[str, Any]

    # Pydantic 모델의 Config 클래스
    class Config:
        from_attributes = True  # Pydantic 모델의 생성자의 인자로 attribute를 받을 수 있게 함


# 새로운 모델: 기존 모델을 상속받고, id 필드 추가
class ScrapManagerWithIDPydantic(ScrapManagerPydantic):
    id: int
