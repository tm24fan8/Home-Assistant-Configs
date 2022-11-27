"""
A collection of lighting effects that runs asynchronously on Philips Hue rooms/groups.
Pyscript must be configured to expose the "hass" global variable and allow all imports
so that we can access the Hue bridge configs and entity registry.
"""
import heapq
import random
import time

import homeassistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

devreg = homeassistant.helpers.device_registry.async_get(hass)
entreg = homeassistant.helpers.entity_registry.async_get(hass)

swarm_groups = {}
# Swarm definitions. Add your own here. To favor a particular color, add multiple instances of it to the palette.
# Max hold is the maximum number of seconds a bulb will hold its setting before transitioning to a new random color.
# The other attributes are self-explanatory, I hope.
swarms = {
    "Christmas": {
        "transition_secs": 10,
        "max_hold_secs": 60,
        "palette": [
            {
                "rgb_color": (255, 0, 0),
                "brightness": 100,
            },
            {
                "rgb_color": (0, 255, 0),
                "brightness": 100,
            },
        ],
    },
    "Bright Christmas": {
        "transition_secs": 1,
        "max_hold_secs": 5,
        "palette": [
            {
                "rgb_color": (255, 13, 24),
                "brightness": 240,
            },
            {
                "rgb_color": (255, 0, 0),
                "brightness": 255,
            },
            {
                "rgb_color": (0, 255, 0),
                "brightness": 255,
            },
            {
                "rgb_color": (21, 255, 13),
                "brightness": 240,
            },
        ],
    },
    "Casino": {
        "transition_secs": 10,
        "max_hold_secs": 60,
        "palette": [
            {
                # Magenta
                "rgb_color": (255, 40, 230),
                "brightness": 214,
            },
            {
                # Blue
                "rgb_color": (70, 82, 255),
                "brightness": 145,
            },
            {
                # Gold
                "rgb_color": (255, 163, 49),
                "brightness": 206,
            },
            {
                # Lavender
                "rgb_color": (115, 56, 255),
                "brightness": 255,
            },
        ],
    },
    "Dim arcade": {
        "transition_secs": 10,
        "max_hold_secs": 60,
        "palette": [
            {
                # White-ish
                "rgb_color": (245, 215, 255),
                "brightness": 88,
            },
            {
                # Blue
                "rgb_color": (64, 29, 255),
                "brightness": 226,
            },
            {
                # Red
                "rgb_color": (255, 71, 44),
                "brightness": 70,
            },
            {
                # Purple
                "rgb_color": (117, 12, 255),
                "brightness": 130,
            },
        ],
    },
    "Neon sea": {
        "transition_secs": 10,
        "max_hold_secs": 60,
        "palette": [
            {
                # Blue 1
                "rgb_color": (65, 8, 255),
                "brightness": 255,
            },
            {
                # Blue 2
                "rgb_color": (64, 10, 255),
                "brightness": 255,
            },
            {
                # Sea green
                "rgb_color": (119, 255, 200),
                "brightness": 255,
            },
        ],
    },
    "Ocean city": {
        "transition_secs": 10,
        "max_hold_secs": 60,
        "palette": [
            {
                # White-ish
                "rgb_color": (255, 246, 250),
                "brightness": 96,
            },
            {
                # Salmon
                "rgb_color": (255, 171, 89),
                "brightness": 130,
            },
            {
                # Light blue
                "rgb_color": (61, 125, 255),
                "brightness": 120,
            },
            {
                # Dark blue
                "rgb_color": (63, 44, 255),
                "brightness": 83,
            },
        ],
    },
    "Murder": {
        "transition_secs": 1,
        "max_hold_secs": 8,
        "palette": [
            {
                "rgb_color": (255, 56, 18),
                "brightness": 55,
            },
            {
                "rgb_color": (255, 53, 4),
                "brightness": 18,
            },
            {
                "rgb_color": (255, 58, 21),
                "brightness": 40,
            },
            {
                "rgb_color": (255, 51, 0),
                "brightness": 54,
            },
        ],
    },
    "Purple rain": {
        "transition_secs": 1,
        "max_hold_secs": 8,
        "palette": [
            {
                "rgb_color": (153, 116, 255),
                "brightness": 110,
            },
            {
                "rgb_color": (195, 67, 255),
                "brightness": 62,
            },
            {
                "rgb_color": (163, 82, 255),
                "brightness": 106,
            },
            {
                "rgb_color": (152, 20, 255),
                "brightness": 80,
            },
        ],
    },
    "Grad party": {
        "transition_secs": 1,
        "max_hold_secs": 30,
        "palette": [
                        {
                            # Blackhawk (sorta)
                            "rgb_color": (64, 0, 255),
                            "brightness": 163,
                        },
                        {
                            # Gold
                            "rgb_color": (255, 205, 49),
                            "brightness": 240,
                        },
                    ]
                    + [
                        {
                            # White
                            "kelvin": 3200,
                            "brightness": 255,
                        },
                    ]
                   * 10,
    },
    "USA": {
        "transition_secs": 3,
        "max_hold_secs": 60,
        "palette": [
            {
                "rgb_color": (255, 0, 0),
                "brightness": 255,
            },
            {
                "rgb_color": (0, 0, 255),
                "brightness": 255,
            },
            {
                "rgb_color": (255, 255, 255),
                "brightness": 255,
            },
        ],
    },
    "Northern lights": {
        "transition_secs": 1,
        "max_hold_secs": 8,
        "palette": [
            {
                "rgb_color": (23, 35, 71),
                "brightness": 255,
            },
            {
                "rgb_color": (2, 83, 133),
                "brightness": 255,
            },
            {
                "rgb_color": (14, 243, 197),
                "brightness": 200,
            },
            {
                "rgb_color": (4, 226, 183),
                "brightness": 200,
            },
            {
                "rgb_color": (3, 132, 152),
                "brightness": 220,
            },
            {
                "rgb_color": (1, 82, 104),
                "brightness": 255,
            },
        ],
    },
    "Summer night": {
        "transition_secs": 10,
        "max_hold_secs": 60,
        "palette": [
            {
                "rgb_color": (160, 82, 255),
                "brightness": 28,
            },
            {
                "rgb_color": (96, 84, 255),
                "brightness": 1,
            },
        ],
    },
    "Candlelight": {
        "transition_secs": 0.25,
        "max_hold_secs": 4,
        "palette": [
            {
                "color_temp": 2300,
                "brightness": 22,
            },
            {
                "color_temp": 2100,
                "brightness": 48,
            },
            {
                "color_temp": 2200,
                "brightness": 67,
            },
            {
                "color_temp": 3200,
                "brightness": 42,
            },
            {
                "color_temp": 1500,
                "brightness": 22,
            },
            {
                "color_temp": 4500,
                "brightness": 70,
            },
        ],
    },
    "Velvet rose": {
        "transition_secs": 10,
        "max_hold_secs": 60,
        "palette": [
            {
                "rgb_color": (255, 125, 162),
                "brightness": 64,
            },
            {
                "rgb_color": (255, 111, 169),
                "brightness": 64,
            },
            {
                "rgb_color": (239, 125, 255),
                "brightness": 64,
            },
            {
                "rgb_color": (255, 134, 116),
                "brightness": 64,
            },
            {
                "rgb_color": (255, 147, 185),
                "brightness": 64,
            },
        ],
    },
    "Halloween": {
        "transition_secs": 4,
        "max_hold_secs": 10,
        "palette": [
            {
                # Orange
                "rgb_color": (247, 95, 28),
                "brightness": 255,
            },
            {
                # Light Orange
                "rgb_color": (255, 154, 0),
                "brightness": 255,
            },
            {
                # Puuuurple
                "rgb_color": (136, 30, 228),
                "brightness": 255,
            },
            {
                # Green
                "rgb_color": (133, 226, 31),
                "brightness": 255,
            },
        ],
    },
}


def light_entities_for_area(tgt_area_name):
    """Find light entity IDs for a specified area. Assumes all lights are color-changing.

    :param tgt_area_name: The HA Area containing the lights.
    :return: Set of light entity IDs for the group name or empty set if no matching group or entities are found.
    """
    log.info(f"Searching for entities in {tgt_area_name}")
    entity_ids = set()
    entities = er.async_entries_for_area(entreg, tgt_area_name)
    if entities:
        entities.extend([e for x in dr.async_entries_for_area(devreg, tgt_area_name) for e in
                        homeassistant.helpers.entity_registry.async_entries_for_device(entreg, x.id)])

    for entity in entities:
        if "light" in entity.entity_id:
            modes = entity.capabilities.get("supported_color_modes")
            log.info(f"Area entity: {entity.id}, modes - {modes}")
            if "hs" in modes:
                entity_ids.add(entity.entity_id)
    return entity_ids


@service
def color_swarm_turn_on(area_id="Office", swarm_name="Christmas"):
    """Start the color swarm effect on the specified Philips Hue light group.

    The color swarm continues running on the group until it is turned off or turned on with different parameters.

    :param area_id: ID Of the HA Area to control. Case-sensitive.
    :param swarm_name: The predefined swarm definition including color palette and transitions.
    """

    if swarm_name not in swarms:
        raise ValueError(f"Swarm '{swarm_name}' does not exist.")
    task.unique(f"color-swarm-{area_id}")
    entity_ids = light_entities_for_area(area_id)
    if entity_ids:
        log.info(
            f"Started '{swarm_name}' color swarm for area '{area_id}' consisting of {len(entity_ids)} light(s)."
        )
    else:
        log.error(f"No light entities found for area '{area_id}'.")
    swarm_groups[area_id] = entity_ids
    # Create a priority queue of the next transition per light, sorted by random future transition times.
    swarm = swarms[swarm_name]
    transition_q = []
    start_time = time.monotonic()
    for entity_id in entity_ids:
        change_time = random.uniform(start_time, start_time + swarm["max_hold_secs"])
        change_color = random.choice(swarm["palette"])
        heapq.heappush(transition_q, (change_time, entity_id, change_color))

    # This will loop forever as long as there are lights and the task isn't killed.
    while transition_q:
        head_time, entity_id, head_color = heapq.heappop(transition_q)
        now = time.monotonic()
        if head_time > now:
            task.sleep(head_time - now)
        light_args = {
            "entity_id": entity_id,
            "transition": swarm["transition_secs"],
            **head_color,
        }
        light.turn_on(**light_args)
        log.debug(f"Applied transition: {light_args}")
        now = time.monotonic()
        next_time = swarm["transition_secs"] + random.uniform(now, now + swarm["max_hold_secs"])
        next_color = random.choice(swarm["palette"])
        heapq.heappush(transition_q, (next_time, entity_id, next_color))


@service
def color_swarm_turn_off(area_id="Office"):
    """Stop any running color swarm effect on the specified area."""
    log.info(f"Stopping swarm: {area_id}")
    task.unique(f"color-swarm-{area_id}")
    if area_id in swarm_groups:
        entities = swarm_groups[area_id]
        for entity in entities:
            light_args = {
                "entity_id": entity,
                "transition": 0
            }
            light.turn_off(**light_args)
        log.info(f"Stopped lights for {len(entities)} lights.")