from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    favorite_cities = relationship("FavoriteCity", back_populates="user", cascade="all, delete-orphan")

    def __str__(self):
        return f"User(name={self.name}, email={self.email})"


class FavoriteCity(Base):
    __tablename__ = "favorite_cities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    city = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "city", name="uq_user_city"),)

    user = relationship("User", back_populates="favorite_cities")