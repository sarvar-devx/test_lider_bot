from sqlalchemy import Boolean, BIGINT, String, ForeignKey, JSON, select, asc, Float, desc, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from db.base import TimeBaseModel, BaseModel, db


class Certificate(BaseModel):
    image_path: Mapped[str] = mapped_column(String(255))


class User(TimeBaseModel):
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[str] = mapped_column(String(64), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(12), nullable=True)
    referrer_id: Mapped[int] = mapped_column(BIGINT, ForeignKey('users.id'), nullable=True)
    referrer: Mapped["User"] = relationship("User", remote_side='User.id')
    user_test_answers: Mapped[list['TestAnswer']] = relationship("TestAnswer", back_populates="user")


class Test(TimeBaseModel):
    name: Mapped[str] = mapped_column(String(255))
    answers: Mapped[dict] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user_test_answers: Mapped[list['TestAnswer']] = relationship("TestAnswer", back_populates="test")


class TestAnswer(TimeBaseModel):
    user_answers: Mapped[dict] = mapped_column(JSON)
    accepted_answers: Mapped[dict] = mapped_column(JSON)
    quality_level: Mapped[float] = mapped_column(Float)

    user_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("users.id", ondelete='CASCADE'))
    user: Mapped['User'] = relationship("User", back_populates="user_test_answers")

    test_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("tests.id", ondelete='CASCADE'))
    test: Mapped['Test'] = relationship("Test", back_populates="user_test_answers")

    @classmethod
    async def get_ordered_test_answers(cls, test_id):
        query = (
            select(cls)
            .where(cls.test_id == test_id)
            .options(selectinload(cls.user))
            .order_by(desc(cls.quality_level), asc(cls.created_at))
        )

        return (await db.execute(query)).scalars().all()


class ReferralMessage(TimeBaseModel):
    photo: Mapped[str] = mapped_column(Text())
    description: Mapped[str] = mapped_column(Text())
