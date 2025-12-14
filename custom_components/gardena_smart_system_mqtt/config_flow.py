"""Config flow for GARDENA smart local MQTT integration."""
import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN


class SmartLocalMQTTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GARDENA smart local MQTT."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get("Gateway ID", ""),
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required("gateway_id", default=""): str,

            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
