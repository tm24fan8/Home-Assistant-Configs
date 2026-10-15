from stubs.pyscript_builtins import state, log, task, event, time_trigger, state_trigger, state_active, service
from stubs.pyscript_generated import input_boolean, light, switch, script, mqtt, input_select, input_text

#! ---------- DAY MODE ----------
# Lists of adaptive lighting switches for different scenarios
ADAPTIVE_DAY = [
    "switch.adaptive_lighting_basement_studio",
    "switch.adaptive_lighting_downstairs_bathroom",
    "switch.adaptive_lighting_emma_bedroom",
    "switch.adaptive_lighting_kallen_bedroom",
    "switch.adaptive_lighting_living_room",
    "switch.adaptive_lighting_master_bedroom",
    "switch.adaptive_lighting_mud_room",
    "switch.adaptive_lighting_tina_lamp",
    "switch.adaptive_lighting_upstairs_bathroom",
    "switch.adaptive_lighting_upstairs_hallway",
    "switch.adaptive_lighting_front_porch"
]

ADAPTIVE_DAY_HOLIDAY = [
    "switch.adaptive_lighting_basement_studio",
    "switch.adaptive_lighting_downstairs_bathroom",
    "switch.adaptive_lighting_emma_bedroom",
    "switch.adaptive_lighting_kallen_bedroom",
    "switch.adaptive_lighting_living_room",
    "switch.adaptive_lighting_master_bedroom",
    "switch.adaptive_lighting_mud_room",
    "switch.adaptive_lighting_tina_lamp",
    "switch.adaptive_lighting_upstairs_bathroom",
    "switch.adaptive_lighting_upstairs_hallway",
]

# List of adaptive lighting sleep mode switches to turn off
ADAPTIVE_SLEEP = [
    "switch.adaptive_lighting_sleep_mode_basement_studio",
    "switch.adaptive_lighting_sleep_mode_downstairs_bathroom",
    "switch.adaptive_lighting_sleep_mode_emma_bedroom",
    "switch.adaptive_lighting_sleep_mode_kallen_bedroom",
    "switch.adaptive_lighting_sleep_mode_living_room",
    "switch.adaptive_lighting_sleep_mode_master_bedroom",
    "switch.adaptive_lighting_sleep_mode_mud_room",
    "switch.adaptive_lighting_sleep_mode_tina_lamp",
    "switch.adaptive_lighting_sleep_mode_upstairs_bathroom",
    "switch.adaptive_lighting_sleep_mode_upstairs_hallway"
]

# List of selected scene input texts to reset to Adaptive
SEL_SCENES_MAIN = [
    "input_text.basement_studio_selected_scene",
    "input_text.downstairs_bathroom_selected_scene",
    "input_text.emma_bedroom_selected_scene",
    "input_text.front_porch_selected_scene",
    "input_text.kallen_bedroom_selected_scene",
    "input_text.living_room_selected_scene",
    "input_text.master_bedroom_selected_scene",
    "input_text.mud_room_selected_scene",
    "input_text.tina_lamp_selected_scene",
    "input_text.upstairs_bathroom_selected_scene",
    "input_text.upstairs_hallway_selected_scene"
]

# Tina's desk reset
SEL_SCENES_TINA_DESK = ["input_text.tina_desk_selected_scene"]

# List of booleans to turn off
BOOLEAN_OFF = [
    "input_boolean.give_me_darkness",
    "input_boolean.goodnight",
    "input_boolean.kallen_computer_updates",
    "input_boolean.night_mode",
    "input_boolean.sunset_lights_triggered"
]

#! ---------- NIGHT MODE ----------
# Booleans to turn on at night
ADAPTIVE_NIGHT = [
    "switch.adaptive_lighting_front_porch"
]

#! ---------- CONSTANTS ----------
EARLY_NIGHT_MODE = "binary_sensor.early_night_mode"
HOLIDAY_MODE = "input_boolean.holiday_mode"
HOLIDAY_HOLD = "input_boolean.holiday_mode_hold"
SUNSET_LIGHTS = "input_boolean.sunset_lights_on"
VACATION = "input_boolean.vacation_mode"
UP_BATH_OCC = "binary_sensor.upstairs_bathroom_occupied"
DESK_LIGHTS = "light.tina_desk_lights"
TRIGGERED = "input_boolean.sunset_lights_triggered"
LIGHT_CHECKS = {
    "living_room": {
        "sensor_entity_id": "sensor.living_room_front_illuminance",
        "threshold_entity_id": "input_number.living_room_lux_threshold"
    },
    "stairwell": {
        "sensor_entity_id": "sensor.stairwell_bottom_illuminance",
        "threshold_entity_id": "input_number.stairwell_lux_threshold"
    },
    "outdoor": {
        "sensor_entity_id": "sensor.home_tempest_illuminance",
        "threshold_entity_id": "input_number.sunset_lights_outdoor_lux_threshold"
    }
}

#! ---------- FUNCTIONS ----------
def light_level_check(sensor_entity_id: str, threshold_entity_id: str) -> bool:
    try:
        below_threshold = float(state.get(sensor_entity_id)) <= float(state.get(threshold_entity_id))
        log.info(f"Light level check for sensor {sensor_entity_id} with threshold {threshold_entity_id}: {below_threshold}")
        return below_threshold
    except (ValueError, TypeError, NameError):
        log.error(f"Error checking light level for sensor {sensor_entity_id} with threshold {threshold_entity_id}")
        return False

def send_lights(time_of_day: str):
    if time_of_day == "day":
        if state.get(HOLIDAY_HOLD) == "off":
            light.turn_off(entity_id="light.front_porch_light")
            log.info("Front porch light turned off for day mode.")
        if state.get(UP_BATH_OCC) == "off":
            light.turn_off(entity_id="light.upstairs_bathroom_lights")
            log.info("Upstairs bathroom lights turned off for day mode.")
    elif time_of_day == "night":
        script.evening_on_first_floor(sunset_lights=1) # pyright: ignore[reportCallIssue]
        script.evening_on_second_floor(sunset_lights=1) # pyright: ignore[reportCallIssue]
        if state.get(DESK_LIGHTS) == "on":
            input_select.select_option(entity_id="input_select.tina_desk_scenes", option="Reset")
            log.info("Tina desk scene reset for night mode.")
        log.info("Night mode lighting adjustments completed.")

def sunrise_booleans_off():
    input_boolean.turn_off(entity_id=BOOLEAN_OFF) # pyright: ignore[reportArgumentType]
    log.info("Sunrise input booleans turned off.")

def adaptive_switches(time_of_day: str):
    if time_of_day == "day":
        if state.get(HOLIDAY_HOLD) == "on":
            switch_adaptive = ADAPTIVE_DAY_HOLIDAY
        else:
            switch_adaptive = ADAPTIVE_DAY
        switch.turn_on(entity_id=switch_adaptive) # pyright: ignore[reportArgumentType]
        switch.turn_off(entity_id=ADAPTIVE_SLEEP) # pyright: ignore[reportArgumentType]
    elif time_of_day == "night":
        switch_adaptive = ADAPTIVE_NIGHT
        if state.get(HOLIDAY_MODE) == "on":
            switch.turn_off(entity_id=switch_adaptive) # pyright: ignore[reportArgumentType]
        else:
            switch.turn_on(entity_id=switch_adaptive) # pyright: ignore[reportArgumentType]
    log.info(f"Adaptive switches set for {time_of_day} mode.")

def send_notifications():
    if state.get(SUNSET_LIGHTS) == "off":
        notify_title = "Sunset Lights SKIPPED"
        notify_msg = "Lights not on due to nobody home, or toggle shutoff"
        sunset_status = "Skipped"
    else:
        notify_title = "Sunset Lights On"
        notify_msg = "It's getting dark, evening lighting is now active"
        sunset_status = "Light Level Trigger"
    log.info(f"Sunset lights status: {sunset_status}")
    script.text_notify(who="all", title=notify_title, message=notify_msg, type="normal", tag="sunset-lights")
    script.tv_notify(who="all", title=notify_title, message=notify_msg, data={"fontsize": "large", "duration": 3, "transparency": "25%"})

def send_holiday(time_of_day: str):
    current_holiday = state.get("input_select.holiday_animation")
    switch_holiday = f"switch.animated_scene_{current_holiday.lower()}"
    if state.get(HOLIDAY_MODE) == "off":
        log.info("Holiday mode is off, skipping holiday lights.")
    else:
        if time_of_day == "day" and state.get(HOLIDAY_HOLD) == "off":
            log.info(f"Turning off holiday lights for {current_holiday} during the day.")
            switch.turn_off(entity_id=switch_holiday)
        elif time_of_day == "day" and state.get(HOLIDAY_HOLD) == "on":
            log.info(f"Keeping holiday lights for {current_holiday} on during the day, due to holiday hold.")
        elif time_of_day == "night":
            task.sleep(1)
            log.info(f"Turning on holiday lights for {current_holiday} at night.")
            switch.turn_on(entity_id=switch_holiday)

def mqtt_publish(payload: str):
    topic = "house/time/early_night_mode"
    mqtt.publish(topic=topic, payload=payload, retain=True) # pyright: ignore[reportCallIssue]
    log.info(f"MQTT published to topic '{topic}' with payload='{payload}'")

def fire_event(time_of_day: str):
    toggle = "on" if time_of_day == "night" else "off"
    event.fire(event_type="extraLights", toggle=toggle)
    log.info(f"Extra lights event fired with toggle={toggle}")

def reset_scenes():
    input_text.set_value(entity_id=SEL_SCENES_MAIN, value="Adaptive") # pyright: ignore[reportArgumentType]
    input_text.set_value(entity_id=SEL_SCENES_TINA_DESK, value="Day Mode") # pyright: ignore[reportArgumentType]
    log.info("Scenes have been reset to default values.")

def sunset(trigger_mode: str = "automatic"):
    input_boolean.turn_on(entity_id=TRIGGERED)
    time_of_day = "night"
    adaptive_switches(time_of_day)
    send_holiday(time_of_day)
    send_lights(time_of_day)
    fire_event(time_of_day)
    if trigger_mode != "manual":
        send_notifications()

def sunrise(trigger_mode: str = "automatic"):
    time_of_day = "day"
    send_lights(time_of_day)
    sunrise_booleans_off()
    fire_event(time_of_day)
    task.sleep(5)
    adaptive_switches(time_of_day)
    reset_scenes()
    send_holiday(time_of_day)

#! ---------- TRIGGERS ----------
@time_trigger("startup")
def startup():
    while state.get(EARLY_NIGHT_MODE) not in ["on", "off"]:
        log.info(f"Waiting for EARLY_NIGHT_MODE to be set. Current value: {state.get(EARLY_NIGHT_MODE)}")
        task.sleep(60)
    log.info("Sunset lights script started up!")
    log.info(f"Current status: EARLY_NIGHT_MODE={state.get(EARLY_NIGHT_MODE)}, TRIGGERED={state.get(TRIGGERED)}, VACATION={state.get(VACATION)}")
    mqtt_publish(payload=state.get(EARLY_NIGHT_MODE))

@time_trigger("period(sunset - 60m, 5m, sunset + 60m)")
@state_active(f"{EARLY_NIGHT_MODE} == 'on' and {TRIGGERED} == 'off' and {VACATION} == 'off'")
def sunset_lights_trigger():
    if any([light_level_check(**light_check) for light_check in LIGHT_CHECKS.values()]):
        log.info("Sunset trigger activated. Light level below threshold")
        sunset(trigger_mode="automatic")
    else:
        log.info("Sunset trigger activated. Light level not below threshold, trigger skipped.")

@state_trigger(f"{EARLY_NIGHT_MODE} == 'off' and {EARLY_NIGHT_MODE}.old == 'on'")
def morning_lights_trigger():
    mqtt_publish(payload=state.get(EARLY_NIGHT_MODE))
    if state.get(VACATION) == "off":
        log.info("Morning lights trigger activated.")
        sunrise(trigger_mode="automatic")

@state_trigger(f"{EARLY_NIGHT_MODE} == 'on' and {EARLY_NIGHT_MODE}.old == 'off'")
def early_night_mode_activated():
    mqtt_publish(payload=state.get(EARLY_NIGHT_MODE))

#! ---------- SERVICES ----------
@service("pyscript.sunset_lights_manual_trigger")
def sunset_lights_manual_trigger():
    """yaml
name: Sunset Lights Manual Trigger
description: Manually triggers the sunset lights sequence.
    """
    if state.get(TRIGGERED) == "off" and state.get(VACATION) == "off":
        sunset(trigger_mode="manual")
    else:
        log.warning("Sunset lights manual trigger attempted, but conditions not met.")
