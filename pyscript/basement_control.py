from stubs.pyscript_builtins import state, log, task, state_trigger, state_active, service
from stubs.pyscript_generated import climate, input_boolean, script, media_player
from hass_users import get_user_info

# Status entities
OCCUPIED = "binary_sensor.basement_occupied"
NIGHT_MODE = "input_boolean.night_mode"

# Temperature sensors
OUTDOOR_TEMP = "sensor.home_tempest_temperature"
TODAY_HIGH_TEMP = "sensor.todays_high_temp"
BASEMENT_TEMP = "sensor.basement_studio_temperature"

# Control entities
HEATER_ALLOWED = "input_boolean.basement_studio_heat_allowed"

# Climate entities
BASEMENT_CLIMATE = "climate.basement_studio_vtherm"

# Thresholds
LOW_FORECASTED_HIGH_TEMP = 55
LOW_OUTDOOR_TEMP = 40
LOW_BASEMENT_TEMP = 64

#! Authorized personnel only beyond this point
# Helper functions
def control_basement_heater(entity_id: str = BASEMENT_CLIMATE, hvac_mode: str = "heat", preset_mode: str = "activity"):
    climate.set_hvac_mode(entity_id=entity_id, hvac_mode=hvac_mode)
    task.sleep(3)
    climate.set_preset_mode(entity_id=entity_id, preset_mode=preset_mode)

def heater_logic():
    if state.get(HEATER_ALLOWED) == 'on':
        if state.get(TODAY_HIGH_TEMP) < LOW_FORECASTED_HIGH_TEMP:
            control_basement_heater()
            log.info("Basement heater turned on due to occupancy and low forecasted high temperature.")
        elif state.get(OUTDOOR_TEMP) < LOW_OUTDOOR_TEMP:
            control_basement_heater()
            log.info("Basement heater turned on due to occupancy and low current outdoor temperature.")
        elif state.get(BASEMENT_TEMP) < LOW_BASEMENT_TEMP:
            control_basement_heater()
            log.info("Basement heater turned on due to occupancy and low basement temperature.")

def devices_on(hass_user: str | None = None):
    script.tony_desktop_wake()
    media_player.turn_on(entity_id="media_player.basement_tv")
    if state.get("binary_sensor.kallen_desktop_on") == "off" and hass_user:
        title = "Basement On"
        message = "Should I turn on Kallen's computer?"
        tag = "kallen_PC"
        who = hass_user
        type = "alert"
        actions = [
            {
                "action": "KALLEN_PC_YES",
                "title": "Yes",
                "icon": "mdi:thumb-up"
            },
            {
                "action": "KALLEN_PC_NO",
                "title": "No",
                "icon": "mdi:thumb-down"
            }
        ]
        script.text_notify(title=title, message=message, tag=tag, who=who, type=type, actions=actions) # pyright: ignore[reportArgumentType]

# Main Basement On function
def basement_on(reason: str, hass_user: str | None = None):
    heater_logic()
    if reason == "manual":
        devices_on(hass_user=hass_user)
        input_boolean.turn_off(entity_id="input_boolean.basement_briefing_ran")

# Triggers
@state_trigger(f"{OCCUPIED} == 'on'")
@state_active(f"{NIGHT_MODE} == 'off'")
def basement_occupied_on():
    log.info(f"Basement On protocol triggered due to occupancy.")
    basement_on(reason="auto")

@service()
def basement_on_manual(**kwargs):
    """yaml
name: Basement On Manual
description: Manually activate Basement On protocol
"""
    user_id = kwargs['context'].user_id
    hass_user_info = get_user_info(user_id=user_id)
    if hass_user_info:
        hass_user = hass_user_info.get("hass_user")
        log.info(f"Basement On Manual service called by user: {hass_user}")
    else:
        hass_user = None
        log.info("Basement On Manual service called by an automation or unknown user.")
    basement_on(reason="manual", hass_user=hass_user)