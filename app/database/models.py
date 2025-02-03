from sqlalchemy import Column, Integer, String, DateTime, Index, Boolean
from datetime import datetime

from .database import Base


class Food(Base):
    __tablename__ = "foods"
    __table_args__ = (
        Index('ix_storage_time', 'storage_time'),
        Index('ix_expiry_days', 'expiry_days'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    expiry_days = Column(Integer)  # 保质期天数
    storage_time = Column(DateTime, default=datetime.now)
    photo_path = Column(String(200))  # 照片存储路径
    is_deleted = Column(Boolean, default=False)  # 软删除字段