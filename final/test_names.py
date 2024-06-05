import pytest
from names import Names

@pytest.fixture
def new_names():
    """Return a new names instance."""
    return Names()

@pytest.fixture
def name_string_list():
    """Return a list of example names."""
    return ["Alice", "Bob", "Eve"]

@pytest.fixture
def used_names(name_string_list):
    """Return a names instance, after three names have been added."""
    my_name = Names()
    for name in name_string_list:
        my_name.lookup([name])
    return my_name

# Test valid input into get_name_string and query
@pytest.mark.parametrize("name_id, expected_string", [
    (0, "Alice"),
    (1, "Bob"),
    (2, "Eve"),
    (3, None)
])
def test_get_name_string(used_names, new_names, name_id, expected_string):
    """Test if get_string returns the expected string."""
    # Name is present
    assert used_names.get_name_string(name_id) == expected_string
    # Name is absent
    assert new_names.get_name_string(name_id) is None

@pytest.mark.parametrize("name_id, expected_string", [
    (0, "Alice"),
    (1, "Bob"),
    (2, "Eve"),
])
def test_query(used_names, new_names, name_id, expected_string):
    """Test if get_string returns the expected string."""
    # Name is present
    assert used_names.query(expected_string) == name_id
    # Name is absent
    assert new_names.query(expected_string) is None


# Test invalid input into All the functions
def test_unique_error_codes():
    name_manager = Names()
    
    # Test valid input
    error_codes = name_manager.unique_error_codes(5)
    assert list(error_codes) == [0, 1, 2, 3, 4]
    
    error_codes = name_manager.unique_error_codes(3)
    assert list(error_codes) == [5, 6, 7]
    
    # Test invalid input
    with pytest.raises(TypeError):
        name_manager.unique_error_codes("5")

def test_query_raises_exceptions(used_names):
    """Test if query raises expected exceptions."""
    with pytest.raises(TypeError):
        used_names.query(3)
    with pytest.raises(SyntaxError):
        used_names.query('3?')
    with pytest.raises(SyntaxError):
        used_names.query('3')

def test_lookup_raises_exceptions(used_names):
    """Test if lookup raises expected exceptions."""
    with pytest.raises(TypeError):
        used_names.lookup('str')
        used_names.lookup([3])


def test_get_name_string_raises_exceptions(used_names):
    """Test if get_name_string raises expected exceptions."""
    with pytest.raises(TypeError):
        used_names.get_name_string(1.4)
    with pytest.raises(TypeError):
        used_names.get_name_string("hello")
    with pytest.raises(ValueError):
        used_names.get_name_string(-1)
