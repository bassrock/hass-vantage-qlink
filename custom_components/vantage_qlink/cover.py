import math

from homeassistant.components.cover import CoverEntity, ATTR_POSITION
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import (
    DeviceInfo,
    async_entries_for_config_entry,
    async_get as get_device_registry,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .command_client.commands import CommandClient
from .command_client.load import LoadInterface
from .const import CONF_COVERS, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the cover platform."""

    client: CommandClient = hass.data[DOMAIN][entry.entry_id]
    current_device_ids = [
        item.strip() for item in entry.options[CONF_COVERS].split(",")
    ]
    async_add_entities(
        QLinkCover(contractor_number=deviceId, client=client)
        for deviceId in current_device_ids
    )

    # Remove devices no longer present
    await remove_unlisted_devices(hass, entry, current_device_ids=current_device_ids)


async def remove_unlisted_devices(
    hass: HomeAssistant, entry: ConfigEntry, current_device_ids: [str]
):
    registered_devices = async_entries_for_config_entry(
        get_device_registry(hass), entry.entry_id
    )
    device_registry = get_device_registry(hass)

    for device in registered_devices:
        # Assuming the identifiers tuple contains your service's unique ID
        device_unique_id = next(iter(device.identifiers))[1]
        if device_unique_id not in current_device_ids:
            device_registry.async_remove_device(device.id)


class QLinkCover(CoverEntity):
    _level: int = 0

    def __init__(self, contractor_number: int | str, client: CommandClient) -> None:
        super().__init__()
        self._contractor_number = (
            int(contractor_number)
            if contractor_number.isnumeric()
            else str(contractor_number)
        )
        self._client = LoadInterface(client)

    async def async_update(self):
        self._level = await self._client.get_level(self._contractor_number)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={
                (DOMAIN, f"{self._contractor_number}"),
            },
            name=f"Load {self._contractor_number}",
            manufacturer="Vantage",
            model="Load",
            serial_number=f"{self._contractor_number}",
        )

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"vantage_cover_{self._contractor_number}"

    @property
    def is_closed(self) -> bool | None:
        """Return whether the cover is closed, or open."""
        return self._level == 0

    @property
    def current_cover_position(self) -> int | None:
        """Return the current position of the cover."""
        return self._level

    @property
    def should_poll(self) -> bool:
        return True

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        self._level = kwargs.get(ATTR_POSITION, 0)
        await self._client.set_level(self._contractor_number, self._level)
