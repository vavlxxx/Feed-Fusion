from src.repos.base import BaseRepo
from src.models.channels import Channel
from src.repos.mappers.mappers import ChannelMapper


class ChannelRepo(BaseRepo):
    model = Channel
    mapper = ChannelMapper
