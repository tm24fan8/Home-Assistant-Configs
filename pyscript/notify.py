from stubs.pyscript_builtins import state, log, task, state_trigger, state_active, service, time_trigger
from stubs.pyscript_generated import input_boolean, script, media_player, mqtt, notify
from hass_users import get_user_info
from datetime import datetime

AUDIBLE_NOTIFICATIONS = "input_boolean.audible_notifications"
PARENTS_HOME = "binary_sensor.parents_home"
WEATHER_ALERTS = "binary_sensor.audible_weather_alerts_allowed"

BACKEND = {
    "living_room": "alexa", "master_bedroom": "alexa", "basement": "alexa",
    "common": "alexa", "all_bedrooms": "alexa", "alexa_everywhere": "alexa",
    "everywhere": "alexa",
    "kallen_bedroom": "google", "emma_bedroom": "google",
    "kids_bedrooms": "google", "basement_google": "google",
}

QUIET_MSG = "I cannot play notifications in the basement right now, because quiet has been requested"

# room -> (gate entity, refusal message; None keeps the original message)
GATES = {
    "kallen_bedroom": ("input_boolean.kallen_sleeping", "I cannot play notifications in Collin Bedroom right now, because Collin is sleeping"),
    "emma_bedroom": ("input_boolean.emma_sleeping", "I cannot play notifications in Emma Bedroom right now, because Emma is sleeping and you would not like what happens if I wake her up"),
    "master_bedroom": ("input_boolean.master_bedroom_sleeping", "I cannot play notifications in Master Bedroom right now, because someone is sleeping and I do not want to wake them up"),
    "basement": ("input_boolean.studio_quiet", QUIET_MSG),
    "basement_google": ("input_boolean.studio_quiet", QUIET_MSG),
    "common": ("input_boolean.studio_quiet", None),
}

ALIASES = {
    "living_room_echo_dot": "living_room",
    "master_bedroom_echo_dot": "master_bedroom",
    "basement_echo_dot": "basement",
    "kallen_bedroom_google_speaker": "kallen_bedroom",
    "emma_bedroom_google_speaker": "emma_bedroom",
    "common_areas": "common",
}

def normalize(who: str) -> str:
    key = who.lower().replace(" ", "_").removeprefix("media_player.")
    return ALIASES.get(key, key)

def everywhere_target() -> str:
    quiet = state.get("input_boolean.studio_quiet") == "on"
    if state.get("input_boolean.master_bedroom_sleeping") == "on":
        if quiet:
            return "living_room"
        if state.get("binary_sensor.people_sleeping") == "on":
            return "common"
        return "living_room"  # the YAML emits an empty string here, which alexa_voice treats as living room
    return "alexa_no_basement" if quiet else "alexa_everywhere"


def resolve_route(who: str, message: str, type: str, voice: str | None):
    room = normalize(who)
    backend = BACKEND.get(room, "alexa")
    target = room if room in BACKEND else "living_room_echo_dot"

    gate = GATES.get(room)
    if gate and type.lower() != "critical" and state.get(gate[0]) == "on":
        return "alexa", "living_room", gate[1] or message

    if room == "alexa_everywhere":
        target = everywhere_target()
    if voice == "nabu":
        backend = "nabu"
    return backend, target, message


# ----------------------------------- ALEXA HANDLING -----------------------------------
ALEXA_TARGETS = {
    "living_room": "media_player.living_room_echo_dot",
    "master_bedroom": "media_player.master_bedroom_echo_dot",
    "all_bedrooms": "media_player.master_bedroom_echo_dot",
    "basement": "media_player.basement_echo_dot",
    "common": "group.common_areas",
    "alexa_no_basement": "group.alexa_no_basement",
    "alexa_everywhere": "group.alexa_everywhere",
    "everywhere": "group.alexa_everywhere",
}

ALL_ECHOES = [
    "media_player.living_room_echo_dot",
    "media_player.basement_echo_dot",
    "media_player.master_bedroom_echo_dot",
]

def alexa_voice(who: str, message: str, voice: str | None = None, type: str = "normal"):
    critical = type.lower() == "critical"

    if critical:
        media_player.volume_set(entity_id=ALL_ECHOES, volume_level=1.0) # pyright: ignore[reportArgumentType]
        task.sleep(3)

    if (
        not critical
        and who in ("master_bedroom", "master_bedroom_echo_dot", "all_bedrooms")
        and state.get("binary_sensor.people_sleeping") == "on"
    ):
        log.info("People are sleeping and this message is not important")
        return

    target = ALEXA_TARGETS.get(who, ALEXA_TARGETS["living_room"])
    if who in ("everywhere", "alexa_everywhere") and not critical \
            and state.get("input_boolean.studio_quiet") == "on":
        target = ALEXA_TARGETS["alexa_no_basement"]

    notify.alexa_media(
        target=target,
        message=f"<voice name='{voice}'><prosody rate='fast'>{message}</prosody></voice>",
        data={"type": "tts"},
    )

# ----------------------------------- GOOGLE HANDLING -----------------------------------
def google_voice(who: str, message: str, voice: str | None = None, type: str = "normal"):
    pass

# ----------------------------------- NABU CASA HANDLING -----------------------------------
def nabu_voice(who: str, message: str, voice: str | None = None, type: str = "normal"):
    pass

# ----------------------------------- MAIN SERVICE -----------------------------------
# @service()
def speech_engine(who: str, message: str, voice: str | None = None, type: str = "normal"):
    """yaml
description: This is the framework for Jarvis to speak on any/all speakers in the house
fields:
    who:
        name: Who
        description: This determines which speaker, or group of speakers, the message is sent to
        required: true
        example: living_room, basement, basement_google, common_areas, master_bedroom, kallen_bedroom, emma_bedroom, kids_bedrooms, all_bedrooms, alexa_everywhere, everywhere
        selector:
            select:
                options:
                    - living_room
                    - basement
                    - basement_google
                    - common
                    - common_areas
                    - master_bedroom
                    - kallen_bedroom
                    - emma_bedroom
                    - kids_bedrooms
                    - all_bedrooms
                    - alexa_everywhere
                    - everywhere
    message:
        name: Message
        description: This is the message you want Jarvis to read.
        required: true
        example: Type some text and I will read it out loud
        selector:
            text:
                multiline: true
    voice:
        name: Voice
        description: Which voice you would like Jarvis to read in (optional, and only applicable on Alexa devices)
        example: Brian, Emma, Joanna, Amy, Justin, Matthew, Salli
        selector:
            select:
                options:
                    - Brian
                    - Emma
                    - Joanna
                    - Amy
                    - Justin
                    - Matthew
                    - Salli
    type:
        name: Type
        description: What type of message is this? Can override some settings depending on the option selected. Alert bypasses time restrictions but respects volume settings and sleep mode. Weather is similar to alert, but will not play at all if everyone is asleep. Critical bypasses all restrictions, and sets all volumes to max.
        example: normal, alert, weather, critical
        selector:
            select:
                options:
                    - normal
                    - alert
                    - weather
                    - critical
"""
    # Set the voice to the default if not provided
    now = datetime.now()
    voice = voice or state.get("input_select.jarvis_voice")
    log.info(f"Speech engine called with the following parameters: Who: {who}, Message: {message}, Voice: {voice}, Type: {type}")

    mqtt.publish(topic="house/polly/lastmsg", payload=message, retain=True) # pyright: ignore[reportCallIssue]
    mqtt.publish(topic="house/polly/msgtime", payload=now.strftime("%I:%M %p").lstrip("0"), retain=True) # pyright: ignore[reportCallIssue]
    mqtt.publish(topic="house/polly/lastloc", payload=who, retain=True) # pyright: ignore[reportCallIssue]

    if (
        state.get(AUDIBLE_NOTIFICATIONS) == "on"
        or type in ["critical", "Critical", "alert", "Alert"]
        or (type in ["weather", "Weather"] and state.get(WEATHER_ALERTS) == "on")
    ) and state.get(PARENTS_HOME) == "on":
        backend, target, msg = resolve_route(who, message, type, voice)
        VOICES = {"alexa": alexa_voice, "google": google_voice, "nabu": nabu_voice}
        VOICES[backend](who=target, message=msg, voice=voice, type=type)

        if normalize(who) in ("everywhere", "all_bedrooms", "kids_bedrooms"):
            google_voice(who=who, message=message, type=type)

# @time_trigger("startup")
# def speech_engine_startup():
#     log.info("Speech Engine initialized")
