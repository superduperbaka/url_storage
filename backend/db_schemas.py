import datetime as dt

from sqlalchemy import Column, ForeignKey, Integer, String, func, insert, select
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ShortLinks(Base):
    __tablename__ = 'short_links'

    id = Column(Integer, primary_key=True)
    link = Column(String(2048), nullable=False)
    short_name = Column(String(256), nullable=False, index=True, unique=True)


class ShortLinksRedirects(Base):
    __tablename__ = 'short_links_redirects'
    id = Column(Integer, primary_key=True)
    link_id = Column(Integer, ForeignKey('short_links.id'), nullable=False)
    timestamp = Column(TIMESTAMP(True), nullable=False)


def create_link_entry(link: str, short_name: str):
    return insert(ShortLinks).values(
        link=link,
        short_name=short_name,
    )


def get_link_entry(short_name: str):
    return select(
        [ShortLinks]
    ).where(ShortLinks.short_name == short_name)


def create_redirect_entry(link_id: int, timestamp: dt.datetime):
    return insert(ShortLinksRedirects).values(link_id=link_id, timestamp=timestamp)


def get_stat(short_name: str):
    return select(
        func.count().label('count'))\
        .select_from(ShortLinks)\
        .join(ShortLinksRedirects, onclause=ShortLinks.id == ShortLinksRedirects.link_id)\
        .where(ShortLinks.short_name == short_name)


def get_stat_summary():
    return select(
        ShortLinks.short_name, func.count().label('count'))\
        .select_from(ShortLinks)\
        .join(ShortLinksRedirects, onclause=ShortLinks.id == ShortLinksRedirects.link_id)\
        .group_by(ShortLinks.short_name)
