"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
Symbol - encapsulates a symbol and stores its properties.
"""
import sys


class Symbol:

    """Encapsulate a symbol and store its properties.

    Parameters
    ----------
    No parameters.

    Public methods
    --------------
    No public methods.
    """

    def __init__(self, type=None, id=None, line_num=None,
                 char_num=None):
        """Initialise symbol properties."""
        self.type = type
        self.id = id
        self.line_num = line_num
        self.char_num = char_num


class Scanner:

    """Read circuit definition file and translate the characters into symbols.

    Once supplied with the path to a valid definition file, the scanner
    translates the sequence of characters in the definition file into symbols
    that the parser can use. It also skips over comments and irrelevant
    formatting characters, such as spaces and line breaks.

    Parameters
    ----------
    path: path to the circuit definition file.
    names: instance of the names.Names() class.

    Public methods
    -------------
    get_symbol(self): Translates the next sequence of characters into a symbol
                      and returns the symbol.
    display_error_line(self, symbol_obj, error_str):
            Displays an error message at the current symbol with the error_str

    """

    def __init__(self, path, names):
        """Open specified file and initialise reserved words and IDs."""
        self.names = names
        self.current_char = " "
        self.symbol_type_list = [self.COMMA, self.SEMICOLON, self.GREATER,
                                 self.BRACK_OPEN, self.BRACK_CLOSE,
                                 self.NUMBER, self.KEYWORD, self.NAME,
                                 self.DOT, self.COLON, self.EOF
                                 ] = range(11)
        self.keywords_list = ["CLOCK", "SWITCH", "AND", "NAND", "OR",
                              "NOR", "DTYPE", "XOR", "MONITOR", "Q",
                              "QBAR", "CLK", "DATA", "SET", "CLEAR",
                              "DEVICES", "CONNECTIONS", "RC"]
        [self.CLOCK_ID, self.SWITCH_ID, self.AND_ID, self.NAND_ID, self.OR_ID,
         self.NOR_ID, self.DTYPE_ID, self.XOR_ID, self.MONITOR_ID, self.Q_ID,
         self.QBAR_ID, self.CLK_ID, self.DATA_ID, self.SET_ID, self.CLEAR_ID,
         self.DEVICES_ID, self.CONNECTIONS_ID, self.RC_ID
         ] = self.names.lookup(self.keywords_list)

        self.obj_file = self._open_file(path)
        self.hashes = 0
        self.line_num = 0
        self.char_num = 0

    def _open_file(self, file_path):
        """Open and return the file specified by path."""
        extension = file_path.split(".")[-1]
        if extension != "txt":
            print("Error: Incorrect file type")
            sys.exit()
        try:
            obj = open(file_path, "r", encoding='utf-8')
            return obj
        except Exception:
            print("Error: File path does not exist.")
            sys.exit()

    def _next_char(self):
        """Gets next character in the file."""
        char = self.obj_file.read(1)
        self._hash_count()
        self.char_num += 1
        self.current_char = char
        if char == '\n':
            self.line_num += 1
            self.char_num = 0
        return char

    def _next_non_comment_char(self):
        """Assumes that a # was encountered"""
        self._next_char()
        if self.current_char != '#':
            return self.current_char

        while True:
            """ Triple hash = comment everything inbetween them
                This takes priority. """
            if self.hashes == 3:
                self.hashes = 0
                while self.hashes < 3:
                    char = self._next_char()
                    if char == "":
                        return char
                self.hashes = 0
                if self.current_char == '#':
                    self.current_char = self._next_char()
                else:
                    return self.current_char

            elif self.current_char == '\n':   # comment until end of line
                self.current_char = self._next_char()
                if self.current_char != '#':
                    return self.current_char

            elif self.current_char == "":   # EOF case
                return ""

            else:   # go next
                self.current_char = self._next_char()

    def _next_valid_char(self):
        valid_punc = [",", ";", ">", "(", ")", ".", ":", ""]
        cur_char = self.current_char
        while cur_char.isspace() or cur_char == '#':
            self.current_char = self._next_non_comment_char()
            cur_char = self.current_char
            if not cur_char.isalnum() and not cur_char.isspace():
                if cur_char not in valid_punc:
                    print("Error: File contains invalid characters.")
                    print(f"First invalid symbol: {self.current_char}"
                          f"(Line {self.line_num}, Character {self.char_num})")
                    sys.exit()

    def get_symbol(self):
        """Translate the next sequence of characters into a symbol."""

        symbol = Symbol()
        self._next_valid_char()

        symbol.line_num = self.line_num
        symbol.char_num = self.char_num

        char_dict = {
            ",": self.COMMA,
            ";": self.SEMICOLON,
            ">": self.GREATER,
            "(": self.BRACK_OPEN,
            ")": self.BRACK_CLOSE,
            ".": self.DOT,
            ":": self.COLON
        }

        if self.current_char in char_dict.keys():
            symbol.type = char_dict[self.current_char]
            self._next_non_comment_char()

        elif self.current_char == "":   # end of file
            symbol.type = self.EOF
            return symbol

        elif self.current_char.isalpha():
            name_string = self._get_name()
            if name_string in self.keywords_list:
                symbol.type = self.KEYWORD
            else:
                symbol.type = self.NAME
            [symbol.id] = self.names.lookup([name_string])

        elif self.current_char.isdigit():
            symbol.id = self._get_number()
            symbol.type = self.NUMBER

        return symbol

    def _hash_count(self):
        """Called every time next_char is used"""

        if self.current_char == '#':
            self.hashes += 1
        else:
            self.hashes = 0

    def _get_name(self):
        """Finds the next name string in the file.

        A name is defined as a letter followed by some number
        of letters and numbers.

        Returns the name string (or None) and the next non-alnum character.

        Assumes the first character was a letter
        """
        output = ""
        while self.current_char.isalnum():
            output += self.current_char
            self.current_char = self._next_char()
        return output

    def _get_number(self):
        """Finds the next number in the file.

        A number is defined by a non-zero number and then
        any amount of consecutive numbers after that.

        Returns the number and the next non-numeric character.

        Assumes the first character was a non-zero digit
        """
        output = ""
        while self.current_char.isdigit():
            output += self.current_char
            self.current_char = self._next_char()

        return int(output)

    def display_error_line(self, symbol_obj, error_str):
        pos = self.obj_file.tell()
        self.obj_file.seek(0)
        lines = self.obj_file.readlines()
        error_line_num = symbol_obj.line_num
        if error_line_num >= len(lines):
            error_line = ""
        else:
            error_line = lines[error_line_num].rstrip()
        error_char_num = symbol_obj.char_num
        print("\n")
        print(error_line)
        up_arrow = ' '*(error_char_num-1) + '^'
        print(up_arrow)
        print(f"(Line {error_line_num+1}) {error_str}")
        self.obj_file.seek(pos)
