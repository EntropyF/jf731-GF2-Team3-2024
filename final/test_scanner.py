import pytest
from scanner import Scanner
from names import Names

names = Names()
scanner = Scanner("sample_file.txt", names)
scanner2 = Scanner("eg_def_file_2.txt", names)
scanner3 = Scanner("def_file_2_no_comments.txt", names)


def run():
    for i in range(1000):
        scanner._next_valid_char()
        print(scanner.current_char, end='')
        scanner._next_char()


def run2():
    for i in range(30):
        s = scanner.get_symbol()
        print((s.type, s.id))
    print(scanner.names.names)


def run3():
    error_msg = "something goes here idk"
    for i in range(222):
        s = scanner2.get_symbol()
        if i == 175:
            er = s
    print((er.type, er.id))
    scanner2.display_error_line(er, error_msg)


@pytest.mark.parametrize("file, expected", [
    ('sample_file.txt', ['Text', 'MoreTest', 'sample', 'text', 'john',
                         'pork727', 'This', 'is', 'very', 'real', 'idk',
                         'AAAAAAAA', 'one1', 'a', 'a5']),
    ('eg_def_file_2.txt', ['SW1', 'SW2', 'SW3', 'SW4', 'A1', 'A3', 'A4', 'A2',
                           'X1', 'N1', 'N2', 'SW5', 'SW6', 'D1', 'C', 'I1',
                           'I2', 'I3']),
])
def test_names(file, expected):
    names = Names()
    scanned = Scanner(file, names)
    num_old_names = len(scanned.names.names)
    symbol_scanned = None
    while symbol_scanned != 10:  # 10 = EOF char
        symbol_scanned = scanned.get_symbol().type

    new_names = scanned.names.names[num_old_names:]
    assert new_names == expected


@pytest.mark.parametrize("file, expected", [
    ('sample_file.txt', [37, 33, 77, 100, 1, 1, 11, 1, 1]),
    ('eg_def_file_2.txt', [0, 0, 0, 0, 2, 2, 2, 2, 3, 3, 0, 0, 2])
])
def test_get_number(file, expected):
    names = Names()
    scanned = Scanner(file, names)
    symbol_scanned_type = None
    num_list = []
    while symbol_scanned_type != 10:  # 10 = EOF char
        symbol_scanned = scanned.get_symbol()
        symbol_scanned_type = symbol_scanned.type
        if symbol_scanned.type == 5:
            num_list.append(symbol_scanned.id)

    assert num_list == expected


@pytest.mark.parametrize("file, expected", [
    ('comment_testing.txt', 'BeeMovieScript')
])
def test_next_valid_char(file, expected):
    names = Names()
    scanned = Scanner(file, names)
    valid_chars = ''
    while scanned.current_char != "":
        scanned._next_valid_char()
        valid_chars += scanned.current_char
        scanned._next_char()

    assert valid_chars == expected


@pytest.mark.parametrize("char_string, expected", [
    ('###n# ##a###', [1, 2, 3, 0, 1, 0, 1, 2, 0, 1, 2, 3]),
    ('##  ###6## #', [1, 2, 0, 0, 1, 2, 3, 0, 1, 2, 0, 1])
])
def test_hash_count(char_string, expected):  # slight modification of method
    num_char = []
    hashes = 0
    for i in char_string:
        if i == '#':
            hashes += 1
        else:
            hashes = 0
        num_char.append(hashes)

    assert num_char == expected


@pytest.mark.parametrize("file, expected", [
    ('comment_testing.txt', "Bee Movie Script \n  "),
])
def test_next_non_comment_char(file, expected):
    names = Names()
    scanned = Scanner(file, names)
    non_comment_chars = ""
    while scanned.current_char != "":
        scanned._next_non_comment_char()
        non_comment_chars += scanned.current_char

    assert non_comment_chars == expected


@pytest.mark.parametrize("file, expected", [
    ('comment_testing.txt', [(7, 18), (7, 19), (7, 20), (10, None)]),
    ('sample_file.txt', [(7, 18), (7, 19), (7, 20), (7, 21), (5, 37), (7, 22),
                         (7, 23), (1, None), (5, 33), (5, 77), (5, 100),
                         (3, None), (7, 24), (7, 25), (7, 26), (7, 27),
                         (4, None), (7, 28), (1, None), (7, 29), (5, 1),
                         (5, 1), (5, 11), (5, 1), (7, 30), (2, None),
                         (8, None), (7, 31), (5, 1), (7, 32), (7, 24),
                         (7, 21), (7, 25), (7, 29), (7, 30), (10, None)])
])
def test_get_symbol(file, expected):
    names = Names()
    scanned = Scanner(file, names)
    symbol_list = []
    symbol_scanned_type = None
    while symbol_scanned_type != 10:  # 10 = EOF char
        symbol_scanned = scanned.get_symbol()
        symbol_scanned_type = symbol_scanned.type
        symbol_list.append((symbol_scanned_type, symbol_scanned.id))

    assert symbol_list == expected


@pytest.mark.parametrize("file, symbol_error_num, error_msg, expected", [
    ('eg_errors.txt', 5, 'Big number',
     "SWITCH SW1(2), SW2(1);\n           ^\n(Line 7) Big number"),
    ('sample_file.txt', 26, 'This is a dot',
     ">.\n ^\n(Line 18) This is a dot")
])
def test_display_error_line(file, symbol_error_num, error_msg, expected):
    symbol_list = []
    names = Names()
    scanned = Scanner(file, names)
    symbol_scanned_type = None
    while symbol_scanned_type != 10:  # 10 = EOF char
        symbol_scanned = scanned.get_symbol()
        symbol_scanned_type = symbol_scanned.type
        symbol_list.append(symbol_scanned)

    error_symbol = symbol_list[symbol_error_num]

    scanned.obj_file.seek(0)
    lines = scanned.obj_file.readlines()
    error_line_num = error_symbol.line_num
    if error_line_num >= len(lines):
        error_line = ""
    else:
        error_line = lines[error_line_num].rstrip()
    error_char_num = error_symbol.char_num
    up_arr = ' '*(error_char_num-1) + '^'
    combine = f"{error_line}\n{up_arr}\n(Line {error_line_num+1}) {error_msg}"

    assert combine == expected
