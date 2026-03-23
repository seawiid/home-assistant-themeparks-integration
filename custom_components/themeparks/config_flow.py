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
    DESTNAME,
    DOMAIN,
    ID,
    METHOD_GET,
    NAME,
    PARKS,
    PARKNAME,
    PARKSLUG,
    SLUG,
    STEP_PARK,
    STEP_USER,
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Theme Park Wait Times."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise the config flow."""
        self._destinations: dict[str, Any] = {}
        self._selected_destination: str = ""

    async def _async_fetch_destinations(self) -> dict[str, Any]:
        """Fetch destinations from the API.

        Returns a dict of {destination_name: {slug, parks}} where parks is a
        list of {id, name} dicts for each park within the destination.
        """
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
            parks = item.get(PARKS, [])
            if slug and name:
                result[name] = {SLUG: slug, PARKS: parks}

        return result

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1 — select a destination (e.g. Walt Disney World Resort)."""
        if user_input is not None:
            self._selected_destination = user_input[PARKNAME]
            return await self.async_step_park()

        if not self._destinations:
            self._destinations = await self._async_fetch_destinations()

        schema = {vol.Required(PARKNAME): vol.In(sorted(self._destinations.keys()))}
        return self.async_show_form(
            step_id=STEP_USER,
            data_schema=vol.Schema(schema),
            last_step=False,
        )

    async def async_step_park(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2 — select an individual park within the destination."""
        dest_data = self._destinations[self._selected_destination]
        parks = dest_data.get(PARKS, [])

        # Build {park_name: park_id} from the parks list returned by the API.
        park_options: dict[str, str] = {
            park[NAME]: park[ID]
            for park in parks
            if park.get(ID) and park.get(NAME)
        }

        dest_name = self._selected_destination

        def _make_entry(park_name: str, park_id: str):
            # Include the destination name in the title only when the park
            # name alone would be ambiguous (e.g. both Disneyland Paris and
            # Disneyland Resort have a park called "Disneyland Park").
            if park_name == dest_name:
                title = f"Theme Park: {park_name}"
            else:
                title = f"Theme Park: {park_name} ({dest_name})"
            return self.async_create_entry(
                title=title,
                data={PARKSLUG: park_id, PARKNAME: park_name, DESTNAME: dest_name},
            )

        # Single-park destination: skip the selector and create the entry immediately.
        if len(park_options) == 1:
            park_name, park_id = next(iter(park_options.items()))
            return _make_entry(park_name, park_id)

        if user_input is not None:
            park_name = user_input[PARKNAME]
            park_id = park_options[park_name]
            return _make_entry(park_name, park_id)

        schema = {vol.Required(PARKNAME): vol.In(sorted(park_options.keys()))}
        return self.async_show_form(
            step_id=STEP_PARK,
            data_schema=vol.Schema(schema),
            last_step=True,
        )
