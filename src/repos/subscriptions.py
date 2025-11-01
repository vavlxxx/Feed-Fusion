from src.schemas.subscriptions import SubscriptionDTO
from src.repos.base import BaseRepo
from src.models.subscriptions import Subscription
from src.repos.mappers.mappers import SubsMapper


class SubsRepo(BaseRepo[Subscription, SubscriptionDTO]):
    model = Subscription
    mapper = SubsMapper
