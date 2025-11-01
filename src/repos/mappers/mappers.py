from src.repos.mappers.base import DataMapper

from src.models.channels import Channel
from src.models.auth import Token, User
from src.models.news import News
from src.models.subscriptions import Subscription

from src.schemas.subscriptions import SubscriptionDTO
from src.schemas.auth import TokenDTO, UserDTO
from src.schemas.channels import ChannelDTO
from src.schemas.news import NewsDTO


class ChannelMapper(DataMapper):
    model = Channel
    schema = ChannelDTO


class NewsMapper(DataMapper):
    model = News
    schema = NewsDTO


class AuthMapper(DataMapper):
    model = User
    schema = UserDTO


class TokenMapper(DataMapper):
    model = Token
    schema = TokenDTO


class SubsMapper(DataMapper):
    model = Subscription
    schema = SubscriptionDTO
