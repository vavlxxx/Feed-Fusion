from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.schemas.subscriptions import SubscriptionDTO
from src.repos.base import BaseRepo
from src.models.subscriptions import Subscription
from src.repos.mappers.mappers import SubsMapper
from src.schemas.subscriptions import SubscriptionWithUserDTO


class SubsRepo(BaseRepo[Subscription, SubscriptionDTO]):
    model = Subscription
    mapper = SubsMapper

    async def get_all_with_user(self):
        query = select(self.model).options(joinedload(Subscription.user))
        result = await self.session.execute(query)
        return [
            SubscriptionWithUserDTO.model_validate(obj)
            for obj in result.scalars().all()
        ]
