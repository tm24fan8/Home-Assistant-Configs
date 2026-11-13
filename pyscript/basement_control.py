from stubs.pyscript_builtins import state, log, task, state_trigger, state_active, service
from stubs.pyscript_generated import climate, input_boolean, script, media_player, fan, light, timer
from hass_users import get_user_info

# Status entities
OCCUPIED = "binary_sensor.basement_occupied"
NIGHT_MODE = "input_boolean.night_mode"
BASEMENT_DOOR = "binary_sensor.basement_studio_door"

# Studio modes
STUDIO_MODES = ["input_boolean.gaming_mode", "input_boolean.recliner_mode", "input_boolean.studio_quiet"]

# Temperature sensors
OUTDOOR_TEMP = "sensor.home_tempest_temperature"
TODAY_HIGH_TEMP = "sensor.todays_high_temp"
BASEMENT_TEMP = "sensor.basement_studio_temperature"

# Control entities
HEATER_ALLOWED = "input_boolean.basement_studio_heat_allowed"

# Climate entities
BASEMENT_CLIMATE = "climate.basement_studio_vtherm"

#! Authorized personnel only beyond this point
# Helper functions
def turn_off_modes():
    for mode in STUDIO_MODES:
        log.debug(f"Turning off mode: {mode}")
        input_boolean.turn_off(entity_id=mode)

def get_temp(entity_id: str) -> float | None:
    try:
        return float(state.get(entity_id))
    except (ValueError, TypeError, NameError):
        log.warning(f"{entity_id} has no usable reading.")
        return None

def control_basement_heater(entity_id: str = BASEMENT_CLIMATE, hvac_mode: str = "heat", preset_mode: str | None = None):
    log.debug(f"Controlling basement heater with entity_id={entity_id}, hvac_mode={hvac_mode}, preset_mode={preset_mode}")
    climate.set_hvac_mode(entity_id=entity_id, hvac_mode=hvac_mode)
    task.sleep(3)
    if preset_mode:
        log.debug(f"Setting basement heater preset mode to {preset_mode}")
        climate.set_preset_mode(entity_id=entity_id, preset_mode=preset_mode)
    else:
        log.debug("No preset mode specified for basement heater.")

def heater_logic(logic: str):
    if state.get(HEATER_ALLOWED) == 'on':
        log.debug(f"Heater logic invoked with logic={logic}")
        if logic == "startup":
            low_forecasted_high_temp = 55
            low_outdoor_temp = 40
            low_basement_temp = 64
            today_high_temp = get_temp(TODAY_HIGH_TEMP)
            outdoor_temp = get_temp(OUTDOOR_TEMP)
            basement_temp = get_temp(BASEMENT_TEMP)
            hvac_mode = "heat"
            preset_mode = "activity"
            if today_high_temp is None or today_high_temp < low_forecasted_high_temp:
                log.info("Basement heater turned on due to occupancy and low forecasted high temperature.")
            elif outdoor_temp is None or outdoor_temp < low_outdoor_temp:
                log.info("Basement heater turned on due to occupancy and low current outdoor temperature.")
            elif basement_temp is None or basement_temp < low_basement_temp:
                log.info("Basement heater turned on due to occupancy and low basement temperature.")
            else:
                hvac_mode = "off"
                preset_mode = None
                log.info("Basement heater left off due to sufficient temperatures.")
            control_basement_heater(hvac_mode=hvac_mode, preset_mode=preset_mode)
        elif logic == "shutdown":
            outdoor_temp_threshold = 32
            outdoor_temp = get_temp(OUTDOOR_TEMP)
            if outdoor_temp is not None and outdoor_temp > outdoor_temp_threshold:
                control_basement_heater(hvac_mode="off")
                log.info("Basement heater deactivated.")
            else:
                if state.get(NIGHT_MODE) == 'on':
                    preset = "frost"
                else:
                    preset = "activity"
                control_basement_heater(hvac_mode="heat", preset_mode=preset)
                log.info(f"Basement heater activated with preset mode: {preset}.")

def door_wait():
    log.info("Waiting for basement door to open.")
    door_open = task.wait_until(
        state_trigger = f"{BASEMENT_DOOR} == 'on'",
        timeout = 300 # Wait up to 5 minutes for the basement door to open
    )
    if door_open["trigger_type"] == "timeout":
        log.info("Basement door did not open within the timeout period.")
    else:
        log.info("Basement door opened.")

    if state.get("fan.basement_fan") == "on":
        fan.turn_off(entity_id="fan.basement_fan")
        log.info("Basement fan turned off.")
    light.turn_off(entity_id="light.basement_studio_lights")
    log.info("Basement studio lights turned off.")

    log.info("Waiting for basement door to close.")
    door_close = task.wait_until(
        state_trigger = f"{BASEMENT_DOOR} == 'off'",
        timeout = 60 # Wait up to 1 minute for the basement door to close
    )
    if door_close["trigger_type"] == "timeout":
        log.info("Basement door did not close within the timeout period.")
    else:
        log.info("Basement door closed.")
    task.sleep(1)

    timer.cancel(entity_id="timer.basement_studio_door_timer")
    log.info("Basement studio door timer canceled.")

def devices_on(hass_user: str | None = None):
    script.tony_desktop_wake()
    log.info("Tony's desktop wake script called.")
    media_player.turn_on(entity_id="media_player.basement_tv")
    log.info("Basement TV turned on.")
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
        log.info("Kallen's computer startup notification sent.")

def devices_off():
    if state.get("media_player.basement_tv") != "playing":
        media_player.turn_off(entity_id="media_player.basement_tv")
        log.info("Basement TV turned off.")
    if state.get("binary_sensor.kallen_desktop_on") == "on":
        if state.get("input_boolean.kallen_computer_updates") == "off":
            script.kallen_desktop_shutdown()
            log.info("Kallen's desktop shutdown.")
        else:
            script.kallen_desktop_lock()
            input_boolean.turn_off(entity_id="input_boolean.kallen_computer_updates")
            log.info("Kallen's desktop locked due to being flagged for updates.")
    if state.get("binary_sensor.tony_desktop_on") == "on":
        script.text_notify(
            type = "alert",
            who = "tony",
            title = "Basement Shutting Down",
            message = "Would you like to shut down your computer?",
            tag = "tony-pc-shutdown",
            actions = [
                {
                    "action": "TONY_COMPUTER_SHUTDOWN",
                    "title": "Shutdown"
                },
                {
                    "action": "TONY_COMPUTER_LOCK",
                    "title": "Lock"
                },
                {
                    "action": "TONY_COMPUTER_IGNORE",
                    "title": "Do Nothing"
                }
            ]
        )
        log.info("Tony's desktop shutdown notification sent.")

# Main Basement On function
def basement_on(reason: str, hass_user: str | None = None):
    heater_logic(logic="startup")
    if reason == "manual":
        devices_on(hass_user=hass_user)
        input_boolean.turn_off(entity_id="input_boolean.basement_briefing_ran")

def basement_shutdown(mode: str = "full"):
    task.unique("basement_shutdown")
    turn_off_modes()
    heater_logic(logic="shutdown")
    devices_off()
    if mode == "full":
        door_wait()

# Basement On Triggers
@state_trigger(f"{OCCUPIED} == 'on'")
@state_active(f"{NIGHT_MODE} == 'off'")
def basement_occupied_on():
    log.info(f"Basement On protocol triggered due to occupancy.")
    basement_on(reason="auto")

def _basement_on_manual(context):
    user_id = context.user_id
    hass_user_info = get_user_info(user_id=user_id)
    if hass_user_info:
        hass_user = hass_user_info.get("hass_user")
        log.info(f"Basement On Manual service called by user: {hass_user}")
    else:
        hass_user = None
        log.info("Basement On Manual service called by an automation or unknown user.")
    basement_on(reason="manual", hass_user=hass_user)

@state_trigger("input_button.basement_on")
def basement_on_button_pressed(context, value, old_value):
    if value not in ["unavailable", "unknown"] and old_value != "unavailable":
        _basement_on_manual(context)
    else:
        log.debug(f"Basement On button pressed with value={value}, old_value={old_value}")

@service()
def basement_on_manual(context):
    """yaml
name: Basement On Manual
description: Manually activate Basement On protocol
"""
    _basement_on_manual(context)

# Basement Shutdown Triggers
@state_trigger("input_button.basement_shutdown")
def basement_shutdown_button_pressed(value, old_value):
    if value not in ["unavailable", "unknown"] and old_value != "unavailable":
        basement_shutdown()
    else:
        log.debug(f"Basement Shutdown button pressed with value={value}, old_value={old_value}")

@service()
def basement_shutdown_manual(mode: str = "full"):
    """yaml
name: Basement Shutdown Manual
description: Manually activate Basement Shutdown protocol
fields:
    mode:
        description: Full shutdown or abridged?
        example: full
        required: false
        selector:
            select:
                options:
                    - full
                    - abridged
"""
    log.info("Basement Shutdown Manual service called.")
    basement_shutdown(mode)