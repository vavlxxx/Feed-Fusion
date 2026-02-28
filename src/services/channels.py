from src.services.base import BaseService
from src.schemas.channels import (
    ChannelDTO,
    ChannelAddDTO,
    ChannelUpdateDTO,
)
from src.utils.exceptions import (
    ObjectExistsError,
    ChannelExistsError,
    ObjectNotFoundError,
    ChannelNotFoundError,
)


class ChannelService(BaseService):
    async def get_channels_list(self):
        channels = await self.db.channels.get_all()
        return channels

    async def get_channel_by_id(self, channel_id: int):
        try:
            channel = await self.db.channels.get_one(id=channel_id)
        except ObjectNotFoundError as exc:
            raise ChannelNotFoundError from exc
        return channel

    async def add_new_channel(self, data: ChannelAddDTO):
        try:
            channel: ChannelDTO = await self.db.channels.add(data)
        except ObjectExistsError as exc:
            raise ChannelExistsError from exc
        await self.db.commit()
        return channel

    async def update_channel(
        self,
        data: ChannelUpdateDTO,
        channel_id: int,
    ) -> ChannelDTO:
        try:
            await self.db.channels.edit(
                data=data,
                id=channel_id,
                ensure_existence=True,
            )
            await self.db.commit()
        except ObjectNotFoundError as exc:
            raise ChannelNotFoundError from exc
        except ObjectExistsError as exc:
            raise ChannelExistsError from exc
        channel: ChannelDTO = await self.db.channels.get_one(
            id=channel_id
        )
        return channel

    async def delete_channel(self, channel_id: int) -> None:
        try:
            await self.db.channels.delete(id=channel_id)
        except ObjectNotFoundError as exc:
            raise ChannelNotFoundError from exc
        await self.db.commit()
