"""Config flow for Theme Park Wait Times integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.httpx_client import get_async_client

from .const import (
    DESTINATIONS,
    DESTINATIONS_URL,
    DOMAIN,
    METHOD_GET,
    NAME,
    PARKNAME,
    PARKSLUG,
    SLUG,
    STEP_USER,
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Theme Park Wait Times."""

    VERSION = 1
    _destinations: dict[str, Any] = {}

    async def _async_fetch_destinations(self) -> dict[str, str]:
        """Fetch the list of parks from the API. Returns {park_name: slug}."""
        client = get_async_client(self.hass)
        response = await client.request(
            METHOD_GET,
            DESTINATIONS_URL,
            timeout=10,
            follow_redirects=True,
        )
        parkdata = response.json()

        result = {}
        for item in parkdata.get(DESTINATIONS, []):
            slug = item.get(SLUG)
            name = item.get(NAME)
            if slug and name:
                result[name] = slug

        return result

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            park_name = user_input[PARKNAME]
            park_slug = self._destinations[park_name]
            return self.async_create_entry(
                title=f"Theme Park: {park_name}",
                data={
                    PARKSLUG: park_slug,
                    PARKNAME: park_name,
                },
            )

        if not self._destinations:
            self._destinations = await self._async_fetch_destinations()

        schema = {vol.Required(PARKNAME): vol.In(sorted(self._destinations.keys()))}
        return self.async_show_form(
            step_id=STEP_USER,
            data_schema=vol.Schema(schema),
            last_step=True,
        )
