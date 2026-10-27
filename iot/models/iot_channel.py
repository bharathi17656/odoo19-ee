import logging
import secrets

from odoo import api, models
from werkzeug.exceptions import Forbidden


_logger = logging.getLogger(__name__)


class IotChannel(models.AbstractModel):
    _name = 'iot.channel'
    _description = "The Websocket IoT Channel"

    def _is_message_allowed(self, message, message_type):
        if self.env.is_system():
            return True

        if not self.env.user._is_internal():
            return False

        if self.env.user.has_group("iot.group_iot_admin"):
            return True

        if message_type != "iot_action":
            return False

        return message.get("action") != "update_url"

    def get_iot_channel(self):
        """Get the IoT websocket channel name (unique for every company).

        :return: The IoT websocket channel used to send the message
        """
        if not self.env.is_system() and not self.env.user._is_internal():
            return
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        ws_channel = ir_config_parameter.get_param('iot.ws_channel')
        if not ws_channel:
            ws_channel = ir_config_parameter.set_param('iot.ws_channel', f'iot_channel-{secrets.token_hex(16)}')

        return ws_channel

    @api.model
    def send_message(self, message, message_type='iot_action'):
        """Send a message to a device via websocket.

        :param dict message: The message to send to the IoT Box
        :param str message_type: The type of the message (Default: call an action on a device)
        """
        if not self._is_message_allowed(message, message_type):
            raise Forbidden()
        _logger.info("Sending message to IoT channel: %s", message)
        self.env['bus.bus']._sendone(self.get_iot_channel(), message_type, message)
