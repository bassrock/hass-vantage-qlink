"""Config flow for Vantage QLink integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .command_client.commands import CommandClient
from .const import CONF_LIGHTS, CONF_COVERS, DOMAIN

_LOGGER = logging.getLogger(__name__)


STEP_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, description="Port", default=10001): int,
        vol.Optional(CONF_LIGHTS, description="Lights"): str,
        vol.Optional(CONF_COVERS, description="Covers"): str,
    }
)


async def validate_connection(host, port):
    async with CommandClient(host, port, conn_timeout=5) as client:
        await client.command("VER")


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    try:
        await validate_connection(data[CONF_HOST], data[CONF_PORT])
    except:  # noqa: E722
        raise CannotConnect  # noqa: B904

    return


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Vantage QLink."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            try:
                return self.async_create_entry(
                    title=f"Vanatage QLink {user_input[CONF_HOST]}",
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                    },
                    options={
                        CONF_LIGHTS: user_input[CONF_LIGHTS],
                        CONF_COVERS: user_input[CONF_COVERS],
                    },
                )
            except Exception as e:
                errors["base"] = "invalid_list"

        return self.async_show_form(
            step_id="user", data_schema=STEP_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                return self.async_create_entry(
                    title=self.config_entry.title,
                    data=self.config_entry.data,
                    options={
                        CONF_LIGHTS: user_input[CONF_LIGHTS],
                        CONF_COVERS: user_input[CONF_COVERS],
                    },
                )
            except Exception as e:
                errors["base"] = "invalid_list"
            return self.async_create_entry(title="", data=user_input)

        # Pre-fill the form with the existing options
        options = self.config_entry.options
        lights = options.get(CONF_LIGHTS, "")
        covers = options.get(CONF_COVERS, "")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_LIGHTS, default=lights, description="Lights"
                    ): str,
                    vol.Optional(
                        CONF_COVERS, default=covers, description="Covers"
                    ): str,
                }
            ),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
