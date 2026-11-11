from stubs.pyscript_builtins import state, log, task, state_trigger, state_active, time_trigger
from stubs.pyscript_generated import input_boolean, script, mqtt, switch

TWITCH = "sensor.twitch_ironnerd24"
VACATION = "input_boolean.vacation_mode"
PEOPLE_PRESENT = "binary_sensor.people_present"

def mqtt_publish(payload: str):
    topic = "house/studio/live"
    mqtt.publish(topic=topic, payload=payload, retain=True) # pyright: ignore[reportCallIssue]
    log.info(f"MQTT published to topic '{topic}' with payload='{payload}'")

def stream_online():
    mqtt_publish(state.get(TWITCH))
    script.tv_notify(
        who="all",
        title="Stream Starting",
        message="Tony has started a live stream in the studio!",
        data={
            "fontsize": "large",
            "duration": 3,
            "transparency": "30%",
            "color": "indigo"
        })
    input_boolean.turn_on(entity_id=["input_boolean.studio_quiet", "input_boolean.gaming_mode"]) # pyright: ignore[reportArgumentType]
    switch.turn_on(entity_id="switch.basement_echo_dot_do_not_disturb_switch")
    log.info("Stream is online and studio has been configured accordingly")

def stream_offline():
    mqtt_publish(state.get(TWITCH))
    input_boolean.turn_off(entity_id="input_boolean.studio_quiet")
    switch.turn_off(entity_id="switch.basement_echo_dot_do_not_disturb_switch")
    log.info("Stream is offline and studio has been restored to normal state")

@time_trigger("startup")
def startup():
    while state.get(TWITCH) not in ["streaming", "offline"]:
        log.info(f"Waiting for Twitch stream status, current state: {state.get(TWITCH)}")
        task.sleep(60)
    log.info(f"Twitch stream status is now: {state.get(TWITCH)}")
    if state.get(TWITCH) == "streaming" and state.get(VACATION) == "off" and state.get(PEOPLE_PRESENT) == "on":
        stream_online()
    else:
        stream_offline()

@state_trigger(f"{TWITCH} == 'streaming'")
@state_active(f"{VACATION} == 'off' and {PEOPLE_PRESENT} == 'on'")
def trigger_online():
    stream_online()

@state_trigger(f"{TWITCH} == 'offline'")
@state_active(f"{VACATION} == 'off' and {PEOPLE_PRESENT} == 'on'")
def trigger_offline():
    stream_offline()