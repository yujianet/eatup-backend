from sqlalchemy import Column, Integer, String, DateTime, Index, UniqueConstraint, Boolean
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
    is_deleted = Column(Boolean, default=False)  # 新增软删除字段


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    large_category = Column(String(50), nullable=False)  # 大分类名称
    small_category = Column(String(50), nullable=False)  # 小分类名称（唯一组合约束）
    expiry_days = Column(Integer, nullable=False)        # 保质期天数

    # 添加唯一约束，确保同一大分类下小分类不重复
    __table_args__ = (
        UniqueConstraint('large_category', 'small_category', name='uq_large_small'),
    )
