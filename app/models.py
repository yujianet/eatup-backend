from sqlalchemy import Column, Integer, String, DateTime, Index
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
    category_large = Column(String(20))  # 大分类（如：蔬菜、水果）
    category_small = Column(String(20))  # 小分类（如：叶菜、根茎）
    expiry_days = Column(Integer)  # 保质期天数
    storage_time = Column(DateTime, default=datetime.now)
    photo_path = Column(String(200))  # 照片存储路径
