# Home Assistant Theme Parks Integration (Fork)

A Home Assistant custom component that pulls live wait time data from the [ThemeParks.wiki API](https://api.themeparks.wiki/v1) and creates sensor entities for each attraction at a selected theme park.

> **Note on versioning:** The original integration was at v1.1.0 when this fork was created. Version numbers in this fork begin at v1.3.0 to clearly distinguish forked releases from the upstream source.

---

## Changes in this fork (v1.3.0)

- **Resort-based sensor naming** — Sensors are now suffixed with the destination/resort name (e.g. "Disneyland Resort") rather than the individual park name. This prevents entity ID collisions when multiple parks within the same resort share a name — for example, both Disneyland Paris and Disneyland Resort have a park called "Disneyland Park", which previously caused duplicate entity names and `_2` suffixes.
- **Clearer entry titles** — Config entries now show both the park name and destination name where needed (e.g. "Theme Park: Disneyland Park (Disneyland Paris)" vs "Theme Park: Disneyland Park (Disneyland Resort)").

## Changes in this fork (v1.2.0)

- **Two-step park selection** — Setup now asks for a destination first (e.g. "Tokyo Disney Resort"), then presents the individual parks within it (e.g. "Tokyo Disneyland" vs "Tokyo DisneySea"). Each park gets its own integration entry with its own set of sensors. Destinations with only one park skip the second screen automatically.
- **Fixed KeyError crash** — `_handle_coordinator_update` no longer crashes when an attraction disappears from the API between polls. The entity is gracefully marked unavailable instead.
- **Fixed device linking** — Attraction entities are now correctly linked to their parent park device (fixes [#12](https://github.com/danielsmith-eu/home-assistant-themeparks-integration/issues/12)).
- **Added `status` attribute** — Each sensor now exposes the API status (`OPERATING`, `DOWN`, `CLOSED`, `REFURBISHMENT`) as an entity attribute, making automations and template sensors more reliable (addresses [#15](https://github.com/danielsmith-eu/home-assistant-themeparks-integration/issues/15)).
- **Defensive API parsing** — All API field lookups now use `.get()` to avoid crashes on malformed or unexpected responses.

---

## Installation via HACS (Custom Repository)

1. In Home Assistant, go to **HACS → Integrations → ⋮ menu → Custom repositories**.
2. Add your fork URL and set category to **Integration**.
3. Search for "Theme Park Wait Times" in HACS and install.
4. Restart Home Assistant.
5. Go to **Settings → Devices & Services → Add Integration** and search for **Theme Park Wait Times**.
6. Select a destination (resort) from the first dropdown, then select an individual park from the second. Repeat to add multiple parks as separate entries.

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
  - alias: "Alert when Space Mountain wait is short"
    trigger:
      - platform: numeric_state
        entity_id: sensor.space_mountain_disneyland_resort
        below: 20
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.space_mountain_disneyland_resort', 'status') == 'OPERATING' }}"
    action:
      - service: notify.mobile_app
        data:
          message: "Space Mountain wait is only {{ states('sensor.space_mountain_disneyland_resort') }} minutes!"
```

---

## Credits

Forked and maintained by [@seawiid](https://github.com/seawiid/home-assistant-themeparks-integration). Original integration by [@danielsmith-eu](https://github.com/danielsmith-eu/home-assistant-themeparks-integration).
Data provided by [ThemeParks.wiki](https://themeparks.wiki).
