"""MQTT Switch platform for GARDENA smart local MQTT."""
import logging
import json
from typing import Any
from pprint import pformat

from homeassistant.components import mqtt
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, TENANT

logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MQTT switch from a config entry."""
    gateway_id = config_entry.data.get("gateway_id")
    sgtin = "3034F8319C02BF00000000C5"
    index = 0
    logger.info(f"Setup Actuator Entry: gateway_id: {gateway_id}, sgtin: {sgtin}, index: {index}")

    # Create the switch entity
    switch = GardenaSmartActuator(
        hass,
        gateway_id,
        sgtin,
        index,
        config_entry.entry_id
    )
    async_add_entities([switch])


class GardenaSmartActuator(SwitchEntity):
    """Representation of an MQTT Switch."""
    TENANT = "hass"

    def __init__(
        self,
        hass: HomeAssistant,
        gateway_id: str,
        sgtin: str,
        index: int,
        entry_id: str
    ) -> None:
        """Initialize the switch."""
        self.hass = hass
        self._attr_name = gateway_id
        self._attr_unique_id = f"{DOMAIN}_switch_{entry_id}"
        self._attr_is_on = False
        self._unsubscribe = None

        self._gateway_id = gateway_id
        self._sgtin = sgtin
        self._index = index

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT events when entity is added."""

        @callback
        def state_message_received(msg):
            """Handle state updates from the device."""
            payload = msg.payload

            logger.info(f"Received state update: {payload} from {msg.topic}")

            data = json.loads(payload)
            logger.warning("State event received %s", pformat(data))

            if data["op"] == "update" and data["entity"]["path"] == "actuator/0":
                logger.info(f"Actuator in path")
                if data["payload"]["state"]["vi"]:
                    self._attr_is_on = True
                    self.async_write_ha_state()
                else:
                    self._attr_is_on = False
                    self.async_write_ha_state()

            elif data["op"] == "update" and "actuator" in data["payload"] and data["entity"]["path"] == "":
                logger.info(f"path empty")
                if data["payload"]["actuator"]["0"]["state"]["vi"]:
                    self._attr_is_on = True
                    self.async_write_ha_state()
                else:
                    self._attr_is_on = False
                    self.async_write_ha_state()

        # Subscribe to state topic
        state_topic = f"{TENANT}/sta/{self._gateway_id}/{self._sgtin}/#"

        self._unsubscribe = await mqtt.async_subscribe(
            self.hass, state_topic, state_message_received, qos=1
        )
        logger.warning(f"Subscribed to state topic: {state_topic}")

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe when entity is removed."""
        if self._unsubscribe:
            self._unsubscribe()
            logger.info(f"Unsubscribed from state topic")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on by publishing to MQTT."""

        # static topic to start watering for 1 min
        payload_on = f"{{\"session-id\":\"991b1782-0fa0-459c-808b-ca89164ad152\",\"res-topic\":\"{TENANT}/exc-res/bs-da-1013015b-6d69-412a-8cc0-8bf0fc12bb27/991b1782-0fa0-459c-808b-ca89164ad152\",\"payload\":{{\"as\":[\"0=\'16\',1=\'60\'\"]}},\"metadata\":{{}}}}"
        command_topic = f"{TENANT}/exc/{self._gateway_id}/{self._sgtin}/actuator/{self._index}/start"

        logger.warning(f"TURNING ON - Publishing '{payload_on}' to {command_topic}")

        await mqtt.async_publish(
            self.hass,
            command_topic,
            payload_on,
            qos=1,
            retain=False
        )

        # Optimistically update state if no state topic
        # if not self._state_topic:
        #     self._attr_is_on = True
        #     self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off by publishing to MQTT."""

        payload_off = f"{{\"session-id\":\"991b1782-0fa0-459c-808b-ca89164ad152\",\"res-topic\":\"{TENANT}/exc-res/bs-da-1013015b-6d69-412a-8cc0-8bf0fc12bb27/991b1782-0fa0-459c-808b-ca89164ad152\",\"payload\":{{\"as\":[\"0=\'16\',1=\'0\'\"]}},\"metadata\":{{}}}}"
        command_topic = f"{TENANT}/exc/{self._gateway_id}/{self._sgtin}/actuator/{self._index}/start"

        logger.warning(f"TURNING OFF - Publishing '{payload_off}' to {command_topic}")

        await mqtt.async_publish(
            self.hass,
            command_topic,
            payload_off,
            qos=1,
            retain=False
        )

        # Optimistically update state if no state topic
        # if not self._state_topic:
        #     self._attr_is_on = False
        #     self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True
