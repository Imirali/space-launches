import requests as r
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, TEXT, TIMESTAMP
from datetime import datetime, timezone

URL = 'https://ll.thespacedevs.com/2.3.0/launches/upcoming/?limit=100'

class Base(DeclarativeBase):
    pass

class Launch(Base):
    __table_args__ = {'schema': 'raw'}
    __tablename__ = 'launches'
    launch_id: Mapped[str] = mapped_column(primary_key=True)
    payload: Mapped[dict] = mapped_column(JSONB)
    source_endpoint: Mapped[str] = mapped_column(TEXT)
    api_last_updated: Mapped[str] = mapped_column(TIMESTAMP(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))


def get_launch_data(url:str)->dict:
    """Fetches launch data from the specified URL and returns it as a dictionary.       
    """
    try:
        logger.info(f"Sending GET request to {url}")
        response = r.get(url)
        response.raise_for_status()  
        data = response.json()  
        logger.info("Request successful. Data received.")
        return data
    except r.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None


def flattched_data(data: dict, source_endpoint:str = 'upcoming') -> list[dict]:
    """Flattens the nested structure of the launch data and returns a list of dictionaries.
    """
    if not data:
        logger.warning("No data to flatten.")
        return []
    flattened = []
    dt = datetime.now(timezone.utc)
    for launch in data.get('results', []):
        flattened_launch = {
            'launch_id': launch.get('id'),
            'payload': launch,
            'source_endpoint': source_endpoint,
            'api_last_updated': launch.get('last_updated'),
            'fetched_at': dt
        }
        flattened.append(flattened_launch)
    logger.info(f"Flattened {len(flattened)} launches.")
    return flattened

def main():



