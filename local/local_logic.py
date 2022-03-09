# Copyright 2020 Richard Koshak
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This module includes the local logic core class.

Classes: LogicCore, LogicOr
"""
import logging
from abc import abstractmethod
from configparser import NoOptionError
from core.actuator import Actuator
from core.utils import set_log_level, parse_values, is_toggle_cmd


class LogicCore(Actuator):
    """Class from which all local logic capabilities must inherit. Is assumes there
    is a "InputSrc" param and automatically registers to subscribe to that topic
    with all of the passed in connections. A default implementation is provided
    for all but the process_message method which must be overridden.
    """
    #pylint: disable=super-init-not-called
    def __init__(self, connections, params):
        """Initializes the Actuator by storing the passed in arguments as data
        members and registers to subscribe to params("InputSrc").

        Arguments:
        - connections: List of the connections
        - params: lambda that returns value for the passed in key
            "InputSrc": required, where command to trigger the actuator come from
            "EnableSrc" optional, where commands to disable this actuator come from
                                  will disable this actuator on demand via msg OFF,
                                  switch on with msg ON. Is enabled by default
            "Values":     optional,  Alternative values to publish instead of OFF / ON
            "OutputDest": required, where the results from the command are
                          published.
        """
        self.log = logging.getLogger(type(self).__name__)
        self.params = params
        self.connections = connections
        set_log_level(params, self.log)
        self.enabled = True

        self.input_src = [s.strip() for s in params("InputSrc").split(",")]
        self.output_dest = [s.strip() for s in params("OutputDest").split(",")]
        self.values = parse_values(params, ["OFF", "ON"])
        try:
            #optional param EnableSrc
            self.enable_src = params("EnableSrc")
            self._register(self.enable_src, self.on_message)
        except NoOptionError:
            self.enable_src = None

        for src in self.input_src:
            def create_msg_handler(source=src):
                def msg_handler(msg):
                    if self.enabled:
                        self.process_message(msg, source)
                    else:
                        self.log.info("Actuator is disabled, ignoring command!")
                self._register(source, msg_handler)
            create_msg_handler()
    #pylint: enable=super-init-not-called

    @abstractmethod
    def process_message(self, msg, src):
        """Abstract method that will get called when a any 'InputSrc' sends a message
        Implementers should execute the action the Actuator performs.

        Arguments:
            - msg : the message from the 'InputSrc'
            - src : the name of the calling 'InputSrc'
        """

    def on_message(self, msg):
        """Enable or Disable local logic depending on the send msg
        """
        self.enabled = (msg == "ON")
        self.log.info("Received %s command for actuator with InputSrc %s",
                      "enable" if self.enabled else "disable", self.input_src)

    def _publish(self, message, destination, filter_echo=False):
        """Protected method that will publish the passed in message to the
        passed in destination to all the passed in connections.

        Parameter filter_echo is intended to activate a filter for looped back messages
        """
        for conn in self.connections:
            # publish only to local connections
            if conn.is_local_connection():
                conn.publish(message, destination, filter_echo)

class LogicOr (LogicCore):
    """Logical OR gate, can receive from multiple sensors
    and will trigger all configured receivers
    """
    def __init__(self, connections, params):
        """Initializes the Actuator by storing the passed in arguments as data
        members and registers 'InputSrc' and 'EnableSrc' with the given connections

        Arguments:
        - connections: List of the connections
        - params: lambda that returns value for the passed in key
            "InputSrc": required, where command to trigger the actuator come from
            "EnableSrc" optional, where commands to disable this actuator come from
                                  will disable this actuator on demand via msg OFF,
                                  switch on with msg ON. Is enabled by default
            "Values":     Alternative values to publish instead of OFF / ON
            "OutputDest": required, where the results from the command are
                          published.
        """
        super().__init__(connections, params)

        self.src_is_on = {}
        for src in self.input_src:
            self.src_is_on[src] = False
        self.output_activ = False
        self.last_output_state = False

        self.log.info("Configued LogicOr: EnableSrc = %s,"
                      " InputSrc = %s, OutputDest = %s",
                      self.enable_src, self.input_src, self.output_dest)

    def process_message(self, msg, src):
        """Will switch the registered 'OutputDest' corresponding
        to the input message from the calling 'InputSrc'

        Arguments:
            - msg : the message from the 'InputSrc'
            - src : the name of the calling 'InputSrc'
        """
        self.last_output_state = self.output_activ

        if is_toggle_cmd(msg):
            self.output_activ = not self.output_activ
        else:
            self.src_is_on[src] = (msg == "ON")

            # if all InputSrc are OFF -> False
            # else -> True
            self.output_activ = bool(sum(self.src_is_on.values()))

        output = self.values[1] if self.output_activ else self.values[0]
        if self.last_output_state != self.output_activ:
            self.log.info("Received command %s, from %s, forwarding command '%s' to %s",
                           msg, src, output, self.output_dest)

            for dest in self.output_dest:
                self._publish(output, dest)
        else:
            self.log.info("Received command %s, from %s, output %s doesn't change,"
                          " ignoring command!", msg, src, output)
