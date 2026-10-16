from stubs.pyscript_builtins import log

# Mapping of user IDs to user information
user_id_list = {
    "c3909d27048140729f002aaef0391775": {
        "short_name": "tony",
        "first_name": "Tony",
        "last_name": "Stork",
        "hass_user": "tonystork"
    },
    "f387a983651a4321a7411ff8cf36f949": {
        "short_name": "tina",
        "first_name": "Christina",
        "last_name": "Stork",
        "hass_user": "christinastork"
    },
    "879b4c04e32841b3ad1d2763a11b4e70": {
        "short_name": "kallen",
        "first_name": "Kallen",
        "last_name": "Stork",
        "hass_user": "kallenstork"
    }
}

def get_user_info(user_id: str) -> dict | None:
    try:
        return user_id_list.get(user_id)
    except TypeError as e:
        log.error(f"TypeError encountered in function 'get_user_info': {e}")
        return None