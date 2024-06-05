"""Parse the definition file and build the logic network.

Used in the Logic Simulator project to analyse the syntactic and semantic
correctness of the symbols received from the scanner and then builds the
logic network.

Classes
-------
Parser - parses the definition file and builds the logic network.
"""

from enum import Enum, auto


# For autocompletion
# from scanner import Scanner, Symbol
# from devices import Devices, Device
# from network import Network
# from monitors import Monitors
# from names import Names

class Parser:
    """Parse the definition file and build the logic network.

    The parser deals with error handling. It analyses the syntactic and
    semantic correctness of the symbols it receives from the scanner, and
    then builds the logic network. If there are errors in the definition file,
    the parser detects this and tries to recover from it, giving helpful
    error messages.

    Parameters
    ----------
    names: instance of the names.Names() class.
    devices: instance of the devices.Devices() class.
    network: instance of the network.Network() class.
    monitors: instance of the monitors.Monitors() class.
    scanner: instance of the scanner.Scanner() class.

    Public methods
    --------------
    __init__(self, names, devices, network, monitors, scanner):
        Initialise constants.

    parse_network(self):
        Parse the circuit definition file.

        Returns True if there are no errors in the circuit definition file,
        False otherwise.
    """

    def __init__(self, names, devices, network, monitors, scanner):
        """Initialise constants."""
        # assert isinstance(names, Names) #  For autocomplete
        # assert isinstance(devices, Devices) #  For autocomplete
        # assert isinstance(network, Network) #  For autocomplete
        # assert isinstance(monitors, Monitors) #  For autocomplete
        # assert isinstance(scanner, Scanner) #  For autocomplete
        self.names = names
        self.devices = devices
        self.network = network
        self.monitors = monitors
        self.scanner = scanner

        self._device_type_keywords_list = (
            self.scanner.CLOCK_ID,
            self.scanner.SWITCH_ID,
            self.scanner.AND_ID,
            self.scanner.NAND_ID,
            self.scanner.OR_ID,
            self.scanner.NOR_ID,
            self.scanner.DTYPE_ID,
            self.scanner.XOR_ID,
            self.scanner.RC_ID
            )

        self.output_identifier_keywords_list = (
            self.scanner.Q_ID,
            self.scanner.QBAR_ID
        )

        self.input_identifier_keywords_list = (
            self.scanner.CLK_ID,
            self.scanner.DATA_ID,
            self.scanner.SET_ID,
            self.scanner.CLEAR_ID
        )

        # Parsing variables
        self.symbol = None

        # Error variables
        [self.EXPECTED_SYMBOL, self.EXPECTED_KEYWORD,
         self.EXPECTED_DEVICE_INSTANTIATION, self.UNEXPECTED_EOF,
         self.EXPECTED_EOF, self.EXPECTED_CONNECTION,
         self.EXPECTED_NAME_PORT_INPUT,
         self.NETWORK_INPUTS_UNCONNECTED] = self.names.unique_error_codes(8)
        self.error_count = 0
        self.suppressed_errors = []

    def _monitor_output(self, output_id, output_port):
        """Monitor a device with ID output_id at port ID output_port."""
        if self.error_count > 0:
            return False
        # print(f"Monitor output ({output_id}, {output_port})")
        err = self.monitors.make_monitor(output_id, output_port)
        if err == self.monitors.NO_ERROR:
            return True
        else:
            self._handle_error(err)

    def _make_connection(self, output_properties, input_properties):
        """Make a connection between two devices.

        output_properties and input_properties should both be size-2 tuples containing
        respective (device_id, port_id).
        """
        if self.error_count > 0:
            return False
        # print(f"Make connection ({output_properties}, {input_properties})")
        out_id, out_port = output_properties
        in_id, in_port = input_properties
        err = self.network.make_connection(out_id, out_port, in_id, in_port)
        if err == self.network.NO_ERROR:
            return True
        else:
            self._handle_error(err)
            return False

    def _initialise_device(self, device_type_symbol, device_id, qualifier):
        """Initialise a device, given the device type symbol, device ID and qualifier."""
        if self.error_count > 0:
            return False
        # print(f"Initialise device ({device_type}, {device_id}, {qualifier})")
        device_types = {
            self.scanner.AND_ID: self.devices.AND,
            self.scanner.OR_ID: self.devices.OR,
            self.scanner.NAND_ID: self.devices.NAND,
            self.scanner.NOR_ID: self.devices.NOR,
            self.scanner.XOR_ID: self.devices.XOR,
            self.scanner.CLOCK_ID: self.devices.CLOCK,
            self.scanner.SWITCH_ID: self.devices.SWITCH,
            self.scanner.DTYPE_ID: self.devices.D_TYPE,
            self.scanner.RC_ID: self.devices.RC
        }
        assert(device_type_symbol in device_types)

        device_type = device_types[device_type_symbol]
        if qualifier:
            qualifier = int(qualifier)
        if device_type == self.devices.SWITCH:
            if qualifier == 1:
                qualifier = self.devices.HIGH
            elif qualifier == 0:
                qualifier = self.devices.LOW

        err = self.devices.make_device(device_id, device_type, qualifier)

        if err == self.devices.NO_ERROR:
            return True
        else:
            self._handle_error(err)
            return None

    def parse_network(self):
        """Parse the circuit definition file.

        Returns True if there are no errors in the circuit definition file,
        False otherwise.
        """
        self.error_count = 0
        self.symbol = None

        # -- Device instantiation section
        self._get_next_symbol()
        self._expect_keyword(self.scanner.DEVICES_ID)
        self._expect_symbol(self.scanner.COLON)

        while True:
            if self.symbol.type == self.scanner.EOF:
                self._handle_error(self.UNEXPECTED_EOF)
                return self._finish_parsing()
            elif self._symbol_is_keyword(self._device_type_keywords_list):
                self._rule_device_instantiation()
            elif self._symbol_is_keyword(self.scanner.CONNECTIONS_ID):
                break
            else:
                self._handle_error(
                    self.EXPECTED_DEVICE_INSTANTIATION, self.scanner.SEMICOLON)
                if self.symbol.type != self.scanner.EOF:
                    self._get_next_symbol()
                # For testing: Go to EOF after finding incorrect device instantiation line
                # self._handle_error(self.EXPECTED_DEVICE_INSTANTIATION, self.scanner.EOF)
                # return self._finish_parsing()

        # -- Connections section

        # Assert the last read symbol was 'CONNECTIONS':
        #  program should not be here otherwise.
        assert(self._symbol_is_keyword(self.scanner.CONNECTIONS_ID))
        self._expect_keyword(self.scanner.CONNECTIONS_ID)
        self._expect_symbol(self.scanner.COLON)

        while True:
            if self._symbol_is_keyword(self.scanner.MONITOR_ID):
                self._rule_monitor()  # Monitors
                break
            elif self.symbol.type == self.scanner.EOF:
                break  # End of file
            elif self.symbol.type == self.scanner.NAME:
                self._rule_connection()
            else:
                self._handle_error(self.EXPECTED_CONNECTION, self.scanner.SEMICOLON)
                if self.symbol.type != self.scanner.EOF:
                    self._get_next_symbol()

        # Check we have correctly reached end of file.
        # This will check for anything after the Monitor instruction.
        if self.symbol.type != self.scanner.EOF:
            self._handle_error(self.EXPECTED_EOF)

        return self._finish_parsing()

    def _finish_parsing(self):
        """Run at the end of parse_network."""
        if self.error_count == 0:
            if not self.network.check_network():
                self._handle_error(self.NETWORK_INPUTS_UNCONNECTED)
        if self.error_count > 0:
            print()
            print(f"Circuit creation failed due to {self.error_count} detected error(s).")
            print("Circuit creation is abandoned after the first error,")
            print("so subsequent semantic errors are not detected.")
        return (self.error_count == 0)

    def _get_next_symbol(self):
        """Get next symbol from self.scanner and set self.symbol to it.

        Returns False and raises self.UNEXPECTED_EOF error if self.symbol is at EOF.
        """
        if self.symbol is not None and self.symbol.type == self.scanner.EOF:
            self._handle_error(self.UNEXPECTED_EOF)
            return False
        self.symbol = self.scanner.get_symbol()
        # assert isinstance(self.symbol, Symbol)  # For autocomplete

    def _expect_keyword(self, id, stopping_symbol=None):
        """Check self.symbol is a given keyword.

        Go to next symbol if true, raise parsing error and
        optionally move to stopping symbol if false.

        id can either be a Keyword ID or a list of Keyword IDs.
        """
        if self._symbol_is_keyword(id):
            self._get_next_symbol()
            return True
        else:
            self._handle_error(self.EXPECTED_KEYWORD, stopping_symbol, id)
            return False

    def _expect_symbol(self, type, stopping_symbol=None):
        """Check self.symbol is a given symbol type.

        Go to next symbol if True, raise parsing error and
        optionally move to stopping symbol if False.
        """
        if self.symbol.type == type:
            self._get_next_symbol()
            return True
        else:
            self._handle_error(self.EXPECTED_SYMBOL, stopping_symbol, type)
            return False

    def _symbol_is_keyword(self, id):
        """Return True if self.symbol is a keyword with the given ID.

        id can either be a Keyword ID or a list of Keyword IDs.
        """
        if isinstance(id, int):
            return (self.symbol.type == self.scanner.KEYWORD and self.symbol.id == id)
        elif hasattr(id, "__len__"):  # Check id is an array-type
            assert (isinstance(i, int) for i in id)
            return (self.symbol.type == self.scanner.KEYWORD and self.symbol.id in id)
        else:
            raise TypeError("Invalid type for id")

    def _rule_device_instantiation(self):
        """Parse device_instantiation rule."""
        device_type = self.symbol.id
        if self._expect_keyword(self._device_type_keywords_list, self.scanner.SEMICOLON):
            self._rule_one_or_more(self._rule_device_name_init,
                                   sep=self.scanner.COMMA,
                                   stop=self.scanner.SEMICOLON,
                                   args=[device_type])

    def _rule_device_name_init(self, device_type):
        """Parse device_name_init rule."""
        device_name = self._rule_device_identifier()
        if device_name is not None:
            qualifier = None
            if self.symbol.type == self.scanner.BRACK_OPEN:
                self._get_next_symbol()
                qualifier = self.symbol.id
                if self._expect_symbol(self.scanner.NUMBER):
                    self._expect_symbol(self.scanner.BRACK_CLOSE)

            return self._initialise_device(device_type, device_name, qualifier)
        return None

    def _rule_connection(self):
        """Parse connection rule."""
        output_conn = self._rule_output_identifier()
        if output_conn is None:
            self._skip_to_symbol(self.scanner.SEMICOLON)
        elif self._expect_symbol(self.scanner.GREATER, self.scanner.SEMICOLON):
            input_conn = self._rule_input_identifier()
            if input_conn is None:
                self._skip_to_symbol(self.scanner.SEMICOLON)
            else:
                self._make_connection(output_conn, input_conn)

        if not self._expect_symbol(self.scanner.SEMICOLON, self.scanner.SEMICOLON):
            self._get_next_symbol()

    def _rule_monitor(self):
        """Parse monitor rule."""
        self._expect_keyword(self.scanner.MONITOR_ID)
        outputs = self._rule_one_or_more(self._rule_output_identifier,
                                         sep=self.scanner.COMMA,
                                         stop=self.scanner.SEMICOLON)
        for output in outputs:
            if output is not None:
                self._monitor_output(*output)

    def _rule_one_or_more(self, rule_func, sep, stop, args=None):
        """Parse one or more of a rule.

        Rule is given by 'rule_func', with separator symbol type 'sep' and
        stopping symbol type 'stop', also skipped to in case of syntax error.

        Returns an array of the return values of the rules.
        """
        if args is None:
            args = []

        returns = []
        returns.append(rule_func(*args))
        while True:
            if self.symbol.type == sep:
                self._get_next_symbol()
                returns.append(rule_func(*args))
                # Skip to next stop symbol if rule_func returns None.
                if returns[-1] is None and (sep is not None or stop is not None):
                    self._skip_to_symbol(stop)

            elif self.symbol.type == stop:
                self._get_next_symbol()
                break
            elif self.symbol.type == self.scanner.EOF:
                self._handle_error(self.UNEXPECTED_EOF)
                break
            else:
                # Raise an error and move to next stopping symbol
                self._handle_error(self.EXPECTED_SYMBOL, stop, (sep, stop))

        return returns

    def _rule_device_identifier(self):
        """Parse device_identifier rule. Return device_id if successful, None otherwise."""
        device_id = self.symbol.id
        if self._expect_symbol(self.scanner.NAME):
            return device_id
        return None

    def _rule_output_identifier(self):
        """Parse output_identifier rule."""
        device_id = self._rule_device_identifier()
        # Device_id failed.
        if device_id is None:
            self._handle_error(self.network.DEVICE_ABSENT)
            return None
        if not self.devices.get_device(device_id) and self.error_count == 0:
            self._handle_error(self.network.DEVICE_ABSENT)
            return None

        # Optional port identifier
        if self.symbol.type == self.scanner.DOT:
            self._get_next_symbol()
            port_id = self.symbol.id
            if self._expect_keyword(self.output_identifier_keywords_list):
                o_id = None
                if port_id == self.scanner.Q_ID:
                    o_id = self.devices.Q_ID
                else:
                    o_id = self.devices.QBAR_ID
                assert(o_id is not None)
                return [device_id, o_id]
            else:
                return None

        return [device_id, None]

    def _rule_input_identifier(self):
        """Parse input_identifier rule."""
        device_id = self._rule_device_identifier()
        # Device_id failed.
        if device_id is None:
            self._handle_error(self.network.DEVICE_ABSENT)
            return None
        if not self.devices.get_device(device_id) and self.error_count == 0:
            self._handle_error(self.network.DEVICE_ABSENT)
            return None

        id_translation = {
            self.scanner.CLK_ID: self.devices.CLK_ID,
            self.scanner.DATA_ID: self.devices.DATA_ID,
            self.scanner.SET_ID: self.devices.SET_ID,
            self.scanner.CLEAR_ID: self.devices.CLEAR_ID
        }

        # Compulsory port identifier
        if self._expect_symbol(self.scanner.DOT, self.scanner.SEMICOLON):
            if self.symbol.type == self.scanner.NAME:
                port_id = self.symbol.id

                self._get_next_symbol()
                return [device_id, port_id]

            elif self._symbol_is_keyword(self.input_identifier_keywords_list):
                port_id = id_translation[self.symbol.id]
                self._get_next_symbol()
                return [device_id, port_id]
            else:
                self._handle_error(self.EXPECTED_NAME_PORT_INPUT)
        return None

    def _handle_error(self, err, stopping_symbol=None, param=None):
        """Handle a parsing error."""
        self.error_count += 1
        # print(self.symbol.type, self.symbol.id)

        # Display error
        if err not in self.suppressed_errors:
            if err == self.EXPECTED_SYMBOL:
                symbol_strings = ["Comma ','", "Semi-colon ';'", "Greater-than arrow '>'",
                                  "Open bracket '('", "Close bracket ')'", "<number>", "<keyword>",
                                  "<name>", "Dot '.'", "Colon ':'", "EOF (End of File)"]
                if isinstance(param, int):
                    error_str = f"Error: Expected Symbol: {symbol_strings[param]}"
                else:
                    param_str = " or ".join([f"'{symbol_strings[p]}'" for p in param])
                    error_str = f"Error: Expected Symbols: {param_str}"
            elif err == self.EXPECTED_KEYWORD:
                if isinstance(param, int):
                    error_str = f"Error: Expected Keyword: '{self.names.get_name_string(param)}'"
                else:
                    param_str = ", ".join([f"'{self.names.get_name_string(p)}'" for p in param])
                    error_str = f"Error: Expected Keywords: {param_str}"
            elif err == self.EXPECTED_CONNECTION:
                error_str = "\n".join([
                    "Error: Expected either:",
                    " - A device name for a connection.",
                    " - 'MONITOR'."
                    ])
            elif err == self.EXPECTED_DEVICE_INSTANTIATION:
                error_str = "\n".join([
                    "Error: Expected either:",
                    " - A device type for device instantiation.",
                    " - 'CONNECTIONS:' (include before defining connections).",
                    "Future errors of this type have been suppressed."
                    ])
                self.suppressed_errors.append(self.EXPECTED_DEVICE_INSTANTIATION)
            elif err == self.UNEXPECTED_EOF:
                error_str = f"Error: Unexpected end of file (EOF)."
            elif err == self.EXPECTED_EOF:
                error_str = f"Error: Expected end of file (EOF)."
            elif err == self.EXPECTED_NAME_PORT_INPUT:
                error_str = "Error: Invalid input port name following dot."
            elif err == self.NETWORK_INPUTS_UNCONNECTED:
                error_str = "Error: There are unconnected inputs in the network."
            elif err == self.network.INPUT_TO_INPUT:
                error_str = "Error: Attempted to connect an input to an input."
            elif err == self.network.OUTPUT_TO_OUTPUT:
                error_str = "Error: Attempted to connect an output to an output."
            elif err == self.network.INPUT_CONNECTED:
                error_str = "Error: Input already has a connection."
            elif err == self.network.OUTPUT_PORT_ABSENT:
                error_str = "Error: Invalid output port."
            elif err == self.network.INPUT_PORT_ABSENT:
                error_str = "Error: Invalid input port."
            elif err == self.network.DEVICE_ABSENT:
                error_str = "Error: Device has not been defined."
            elif err == self.devices.INVALID_QUALIFIER:
                error_str = "Error: Invalid device qualifier."
            elif err == self.devices.NO_QUALIFIER:
                error_str = "Error: No device qualifier."
            elif err == self.devices.BAD_DEVICE:
                error_str = "Error: Bad device type."
            elif err == self.devices.QUALIFIER_PRESENT:
                error_str = "Error: Device qualifier present when there should be none."
            elif err == self.devices.DEVICE_PRESENT:
                error_str = "Error: Device with this name has already been instantiated."
            elif err == self.monitors.NOT_OUTPUT:
                error_str = "Error: Not a valid output for this device."
            elif err == self.monitors.MONITOR_PRESENT:
                error_str = "Error: An output is being monitored more than once."
            else:
                error_str = f"Got error : {err}"

            self.scanner.display_error_line(self.symbol, error_str)

        if stopping_symbol is not None:
            self._skip_to_symbol(stopping_symbol)

    def _skip_to_symbol(self, stopping_symbol):
        """Skip to next stopping symbol or EOF.

        stopping_symbol can be a Symbol or array of Symbols.
        """
        if hasattr(stopping_symbol, "__len__"):  # Check stopping_symbol is an array-type
            while ((self.symbol.type not in stopping_symbol)
                   and self.symbol.type != self.scanner.EOF):
                self._get_next_symbol()
        elif isinstance(stopping_symbol, int):
            while (self.symbol.type != stopping_symbol
                   and self.symbol.type != self.scanner.EOF):
                self._get_next_symbol()
        else:
            raise TypeError("Invalid type for stopping_symbol.")
