"""Platform for Theme Park sensor integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, ID, NAME, STATUS, TIME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    my_api = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = ThemeParksCoordinator(hass, my_api, config_entry.entry_id)

    await coordinator.async_config_entry_first_refresh()

    entities = [
        AttractionSensor(coordinator, idx)
        for idx in coordinator.data.keys()
    ]

    _LOGGER.info(
        "Adding %d attraction entities for entry %s",
        len(entities),
        config_entry.entry_id,
    )
    async_add_entities(entities)


class AttractionSensor(SensorEntity, CoordinatorEntity):
    """Sensor entity for a single theme park attraction."""

    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: "ThemeParksCoordinator", idx: str) -> None:
        """Initialize the attraction sensor."""
        super().__init__(coordinator)
        self.idx = idx

        data = coordinator.data[idx]
        self._attr_name = data[NAME]
        self._attr_unique_id = f"{coordinator.entry_id}_{data[ID]}"
        self._attr_native_value = data[TIME]
        self._attr_extra_state_attributes = {
            "status": data.get(STATUS),
            "attraction_id": idx,
        }

        _LOGGER.debug("Initialised AttractionSensor: %s", self._attr_name)

    @property
    def device_info(self) -> DeviceInfo:
        """Link this entity to the park device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry_id)},
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.idx not in self.coordinator.data:
            # Attraction has disappeared from the API response.
            _LOGGER.warning(
                "Attraction '%s' (%s) no longer in API data — marking unavailable",
                self._attr_name,
                self.idx,
            )
            self._attr_available = False
            self.async_write_ha_state()
            return

        self._attr_available = True
        data = self.coordinator.data[self.idx]
        self._attr_native_value = data[TIME]
        self._attr_extra_state_attributes = {
            "status": data.get(STATUS),
            "attraction_id": self.idx,
        }

        _LOGGER.debug(
            "Updated %s: wait_time=%s, status=%s",
            self._attr_name,
            self._attr_native_value,
            self._attr_extra_state_attributes.get("status"),
        )
        self.async_write_ha_state()


class ThemeParksCoordinator(DataUpdateCoordinator):
    """Coordinator that polls the ThemeParks.wiki live endpoint."""

    def __init__(self, hass: HomeAssistant, api, entry_id: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Theme Park Wait Time Sensor",
            update_interval=timedelta(minutes=5),
        )
        self.api = api
        self.entry_id = entry_id

    async def _async_update_data(self) -> dict:
        """Fetch fresh data from the API."""
        _LOGGER.debug("Polling ThemeParks API")
        return await self.api.do_live_lookup()
