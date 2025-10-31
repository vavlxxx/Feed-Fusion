from src.repos.mappers.base import DataMapper

from src.models.channels import Channel
from src.schemas.channels import ChannelDTO
from src.models.news import News
from src.schemas.news import NewsDTO


class ChannelMapper(DataMapper):
    model = Channel
    schema = ChannelDTO


class NewsMapper(DataMapper):
    model = News
    schema = NewsDTO
