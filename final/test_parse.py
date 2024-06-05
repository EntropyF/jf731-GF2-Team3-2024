# Extra tests for parser
import pytest
from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner, Symbol
from parse import Parser
from userint import UserInterface
from gui import Gui

# Placeholder instances
n = Names()
s = Scanner("test_parse/empty.txt", n)


@pytest.fixture()
def skeleton_scanner():
    """Return a new Scanner instance with a placeholder get_symbol()."""
    names = Names()
    scanner = Scanner("test_parse/empty.txt", names)
    scanner.count = 0
    scanner.symbols = [Symbol(scanner.KEYWORD, scanner.DEVICES_ID)]

    def new_get_symbol_wrapper(self):
        def new_get_symbol():
            self.count += 1
            if self.count > len(self.symbols):
                return Symbol(self.EOF)
            return self.symbols[self.count - 1]
        return new_get_symbol
    scanner.get_symbol = new_get_symbol_wrapper(scanner)

    def new_error_line(symbol, error_str):
        print("Error")
        print(symbol.type, symbol.id, symbol.line_num, symbol.char_num)
        print(error_str)
    scanner.display_error_line = new_error_line
    return scanner


@pytest.fixture
def new_parser(skeleton_scanner):
    """Reutrn a new Parser instance with placeholder scanner."""
    names = skeleton_scanner.names
    devices = Devices(names)
    network = Network(names, devices)
    monitors = Monitors(names, devices, network)
    parser = Parser(names, devices, network, monitors, skeleton_scanner)
    return parser


@pytest.mark.parametrize("symbols, errs", [
    ([
        Symbol(s.KEYWORD, s.DEVICES_ID),
        Symbol(s.COLON),
        Symbol(s.KEYWORD, s.CONNECTIONS_ID),
        Symbol(s.COLON)
    ], 0),
    ([Symbol(s.KEYWORD, s.DEVICES_ID)], 2),
    ([
        Symbol(s.KEYWORD, s.DEVICES_ID),
        Symbol(s.COLON),
        Symbol(s.KEYWORD, s.CONNECTIONS_ID),
        Symbol(s.COLON),
        Symbol(s.KEYWORD, s.MONITOR_ID),
        Symbol(s.SEMICOLON)
    ], 2),
    ([
        Symbol(s.KEYWORD, s.DEVICES_ID),
        Symbol(s.COLON),
        Symbol(s.KEYWORD, s.CONNECTIONS_ID),
        Symbol(s.COLON),
        Symbol(s.KEYWORD, s.MONITOR_ID)
    ], 3),

])
def test_parse_network(new_parser, symbols, errs):
    """Test parse_network."""
    s = new_parser.scanner
    s.symbols = symbols
    new_parser.parse_network()
    assert(new_parser.error_count == errs)
    assert(new_parser._finish_parsing() == (new_parser.error_count == 0))


def test_expected_eof():
    """Test for expected EOF error."""
    names = Names()
    scanner = Scanner("test_parse/expected_eof.txt", names)
    devices = Devices(names)
    network = Network(names, devices)
    monitors = Monitors(names, devices, network)
    parser = Parser(names, devices, network, monitors, scanner)
    scanner.errs = []

    def error_func(symbol, err_str):
        scanner.errs.append([symbol, err_str])
    scanner.display_error_line = error_func
    parser.parse_network()
    assert(parser.error_count == 1)
    assert(scanner.errs[0][0].type == scanner.NAME)


def test_invalid_qualifier():
    """Test for invalid qualifier."""
    names = Names()
    scanner = Scanner("test_parse/invalid_qualifier.txt", names)
    devices = Devices(names)
    network = Network(names, devices)
    monitors = Monitors(names, devices, network)
    parser = Parser(names, devices, network, monitors, scanner)
    scanner.errs = []

    def error_func(symbol, err_str):
        scanner.errs.append([symbol, err_str])
    scanner.display_error_line = error_func
    parser.parse_network()
    print(scanner.errs)
    assert(parser.error_count == 1)
    assert(scanner.errs[0][0].type == scanner.SEMICOLON)
    assert(scanner.errs[0][1] == 'Error: Invalid device qualifier.')


def test_missing_semicolon():
    """Test for missing semicolons."""
    names = Names()
    scanner = Scanner("test_parse/missing_semicolon.txt", names)
    devices = Devices(names)
    network = Network(names, devices)
    monitors = Monitors(names, devices, network)
    parser = Parser(names, devices, network, monitors, scanner)
    scanner.errs = []

    def error_func(symbol, err_str):
        scanner.errs.append([symbol, err_str])
    scanner.display_error_line = error_func
    parser.parse_network()
    # print([scanner.errs[i][0].type for i in range(len(scanner.errs))])
    # print(scanner.errs)
    assert(parser.error_count == 4)
    assert(scanner.errs[0][0].type == scanner.KEYWORD)
    assert(scanner.errs[0][0].id == scanner.NAND_ID)
    assert(scanner.errs[1][0].type == scanner.NAME)
    assert(scanner.errs[2][0].type == scanner.NAME)
    assert(scanner.errs[3][0].type == scanner.EOF)
    assert(scanner.errs[3][1] == 'Error: Unexpected end of file (EOF).')


def test_missing_connections():
    """Test for missing connections i.e. inputs not fully connected."""
    names = Names()
    scanner = Scanner("test_parse/missing_connections.txt", names)
    devices = Devices(names)
    network = Network(names, devices)
    monitors = Monitors(names, devices, network)
    parser = Parser(names, devices, network, monitors, scanner)
    scanner.errs = []

    def error_func(symbol, err_str):
        scanner.errs.append([symbol, err_str])
    scanner.display_error_line = error_func
    parser.parse_network()
    assert(parser.error_count == 1)
