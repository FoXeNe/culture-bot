import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

# создаем тут что бы был один объект на весь поект
engine = create_async_engine(DATABASE_URL)

# создаются сессии, expire_on_commit=false что бы после коммита они жили
async_session = async_sessionmaker(engine, expire_on_commit=False)


# отдает сессию и сама ее закрывает
async def get_session():
    async with async_session() as session:
        yield session
