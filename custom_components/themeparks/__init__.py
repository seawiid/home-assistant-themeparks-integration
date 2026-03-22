"""The Theme Park Wait Times integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.httpx_client import get_async_client

from .const import (
    DOMAIN,
    ENTITY_BASE_URL,
    ENTITY_TYPE,
    ID,
    LIVE,
    LIVE_DATA,
    METHOD_GET,
    NAME,
    PARKNAME,
    PARKSLUG,
    QUEUE,
    STANDBY,
    STATUS,
    TIME,
    TYPE_ATTRACTION,
    TYPE_SHOW,
    WAIT_TIME,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Theme Park Wait Times from a config entry."""
    data = hass.data.setdefault(DOMAIN, {})

    api = ThemeParkAPI(hass, entry)
    await api.async_initialize()

    data[entry.entry_id] = api

    # Register the park as a device so attraction entities can link to it.
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="ThemeParks.wiki",
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class ThemeParkAPI:
    """Wrapper for theme parks API."""

    ha_device_registry: dr.DeviceRegistry
    ha_entity_registry: er.EntityRegistry

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the API wrapper."""
        self._hass = hass
        self._config_entry = config_entry
        self._parkslug = config_entry.data[PARKSLUG]
        self._parkname = config_entry.data[PARKNAME]

    async def async_initialize(self) -> None:
        """Initialize registries."""
        self.ha_device_registry = dr.async_get(self._hass)
        self.ha_entity_registry = er.async_get(self._hass)

    async def do_live_lookup(self) -> dict:
        """Fetch live wait time data for all attractions in this park."""
        _LOGGER.debug("Running do_live_lookup for park: %s", self._parkname)

        items = await self.do_api_lookup()

        result = {}
        for item in items:
            attraction_id = item.get(ID)
            if not attraction_id:
                _LOGGER.debug("Skipping item with no ID: %s", item)
                continue

            raw_name = item.get(NAME, "Unknown Attraction")
            name = f"{raw_name} ({self._parkname})"
            status = item.get(STATUS)

            _LOGGER.debug("Parsed API item: %s (status=%s)", raw_name, status)

            queue = item.get(QUEUE, {})
            standby = queue.get(STANDBY, {}) if queue else {}
            wait_time = standby.get(WAIT_TIME) if standby else None

            result[attraction_id] = {
                ID: attraction_id,
                NAME: name,
                TIME: wait_time,
                STATUS: status,
            }

        return result

    async def do_api_lookup(self):
        """Fetch live data from the ThemeParks.wiki API."""
        url = f"{ENTITY_BASE_URL}/{self._parkslug}/{LIVE}"

        client = get_async_client(self._hass)
        response = await client.request(
            METHOD_GET,
            url,
            timeout=30,
            follow_redirects=True,
        )

        items_data = response.json()
        live_data = items_data.get(LIVE_DATA, [])

        return [
            item
            for item in live_data
            if item.get(ENTITY_TYPE) in (TYPE_ATTRACTION, TYPE_SHOW)
        ]
