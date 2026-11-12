from stubs.pyscript_builtins import state, log, task, state_trigger, state_active, time_trigger
from stubs.pyscript_generated import scene, light, lifx, switch, script

DOORBELL = "binary_sensor.front_doorbell_ding_mqtt"
FRONT_DOOR = "binary_sensor.front_door"
PEOPLE_HOME = "binary_sensor.parents_home"
MAIN_TIMEOUT = 30
BASEMENT_TIMEOUT = 10

def build_config() -> tuple[str, list[str], str, list[str], bool]:
    led_strip = False
    lights_scene = "doorbell_lights_restore"
    lights_list = ["light.living_room_overhead","light.tina_lamp_top"]
    try:
        led_strip = state.get("light.living_room_led_strip") not in ["unavailable", "unknown"]
    except NameError:
        led_strip = False
    if led_strip:
        lights_list.append("light.living_room_led_strip")
        log.info("LED strip detected and added to lights list")

    adaptive_scene = "doorbell_adaptive_restore"
    adaptive_list = ["switch.adaptive_lighting_tina_lamp","switch.adaptive_lighting_living_room"]
    return lights_scene, lights_list, adaptive_scene, adaptive_list, led_strip

def backup_scenes(scene_id: str, entity_list: list[str]):
    snapshot_entities = ",".join(entity_list)
    scene.create(scene_id=scene_id, snapshot_entities=snapshot_entities)

@time_trigger("startup")
def startup():
    state.set("pyscript.doorbell_lights_backup_active", "off")
    log.info("Doorbell watcher activated, scene backup monitor created")

@state_trigger(f"{DOORBELL} == 'on'")
@state_active(f"{PEOPLE_HOME} == 'on'")
def doorbell_ring():
    task.unique("doorbell_ring")
    log.info("Doorbell ring detected")

    lights_scene, lights_list, adaptive_scene, adaptive_list, led_strip = build_config()
    lights = ",".join(lights_list)
    adaptive = ",".join(adaptive_list)

    backup_active = state.get("pyscript.doorbell_lights_backup_active")
    if backup_active != "on":
        state.set("pyscript.doorbell_lights_backup_active", "on")
        backup_scenes(lights_scene, lights_list)
        backup_scenes(adaptive_scene, adaptive_list)
        log.info("Current lights and adaptive lighting state backed up")
    else:
        log.info("Lights and adaptive lighting state already backed up")

    switch.turn_off(entity_id=adaptive)
    light.turn_on(entity_id=lights, color_name="green")
    if led_strip:
        try:
            lifx.effect_pulse(entity_id="light.living_room_led_strip",
                                mode="ping",
                                period=1,
                                cycles=30,
                                color_name="white",
                                brightness=255)
        except Exception as e:
            log.warning(f"LED strip pulse failed: {e}")
    log.info("Doorbell lights and effects activated on first floor")

    if state.get("light.basement_studio_lights") == "on" and state.get("input_boolean.studio_quiet") == "off":
        script.turn_on(
            entity_id="script.basement_lights_alert",
            variables={"duration": BASEMENT_TIMEOUT, "type": "green"} # pyright: ignore[reportCallIssue]
        )
        log.info(f"Basement lights alert activated for {BASEMENT_TIMEOUT} seconds")

    log.info(f"Waiting for front door to open or timeout of {MAIN_TIMEOUT} seconds")
    result = task.wait_until(
        state_trigger=f"{FRONT_DOOR} == 'on'",
        timeout=MAIN_TIMEOUT
    )
    if result["trigger_type"] == "timeout":
        log.info(f"Resetting lights, adaptive lighting, and effects due to door not opening within {MAIN_TIMEOUT} seconds")
    else:
        log.info("Front door opened...resetting lights, adaptive lighting, and effects")

    scene.turn_on(entity_id=f"scene.{lights_scene}")
    task.sleep(3)
    if led_strip:
        try:
            lifx.effect_stop(entity_id="light.living_room_led_strip")
        except Exception as e:
            log.warning(f"LED strip effect stop failed: {e}")
    scene.turn_on(entity_id=f"scene.{adaptive_scene}")
    log.info("Doorbell lights and adaptive lighting reset completed")
    state.set("pyscript.doorbell_lights_backup_active", "off")
    log.info("Doorbell lights backup flag deactivated")