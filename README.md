# Home Assistant Theme Parks Integration (Fixed Fork)

A Home Assistant custom component that pulls live wait time data from the [ThemeParks.wiki API](https://api.themeparks.wiki/v1) and creates sensor entities for each attraction at a selected theme park.

## Changes in this fork (v1.2.0)

- **Fixed KeyError crash** — `_handle_coordinator_update` no longer crashes when an attraction disappears from the API between polls. The entity is gracefully marked unavailable instead.
- **Fixed device linking** — Attraction entities are now correctly linked to their parent park device (fixes [#12](https://github.com/danielsmith-eu/home-assistant-themeparks-integration/issues/12)).
- **Added `status` attribute** — Each sensor now exposes the API status (`OPERATING`, `DOWN`, `CLOSED`, `REFURBISHMENT`) as an entity attribute, making automations and template sensors more reliable (addresses [#15](https://github.com/danielsmith-eu/home-assistant-themeparks-integration/issues/15)).
- **Defensive API parsing** — All API field lookups now use `.get()` to avoid crashes on malformed or unexpected responses.
- **Config flow cleanup** — Minor defensive improvements to park list fetching.

---

## Installation via HACS (Custom Repository)

1. In Home Assistant, go to **HACS → Integrations → ⋮ menu → Custom repositories**.
2. Add your fork URL and set category to **Integration**.
3. Search for "Theme Park Wait Times" in HACS and install.
4. Restart Home Assistant.
5. Go to **Settings → Devices & Services → Add Integration** and search for **Theme Park Wait Times**.
6. Select your park from the dropdown and confirm.

## Manual Installation

1. Copy the `custom_components/themeparks` folder into your HA `config/custom_components/` directory.
2. Restart Home Assistant.
3. Add the integration via **Settings → Devices & Services**.

---

## Entities

Each attraction becomes a sensor:

| Attribute | Description |
|-----------|-------------|
| State | Current standby wait time in minutes (`None` if no queue data) |
| `status` | API status: `OPERATING`, `DOWN`, `CLOSED`, `REFURBISHMENT` |
| `attraction_id` | UUID from ThemeParks.wiki |

Sensors update every **5 minutes**. If an attraction no longer appears in the API response it is marked **unavailable** rather than crashing.

## Example automation

```yaml
automation:
  - alias: "Alert when Space Mountain is short"
    trigger:
      - platform: numeric_state
        entity_id: sensor.space_mountain_magic_kingdom
        below: 20
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.space_mountain_magic_kingdom', 'status') == 'OPERATING' }}"
    action:
      - service: notify.mobile_app
        data:
          message: "Space Mountain wait is only {{ states('sensor.space_mountain_magic_kingdom') }} minutes!"
```

---

## Credits

Forked and maintained by [@seawiid](https://github.com/seawiid/home-assistant-themeparks-integration). Original integration by [@danielsmith-eu](https://github.com/danielsmith-eu/home-assistant-themeparks-integration).
Data provided by [ThemeParks.wiki](https://themeparks.wiki).
