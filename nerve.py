"""Nerve firmware specific code.
"""


def extract_value(
    data_string: str, key: str, definer: str = "=", delimiter: str = ","
) -> str | None:
    """Extract XBee messages formatted in Nerve's XBee driver format.

    Args:
        data_string: String to search data value in.
        key: Key value to find value of.
        definer: Substring used to separate end of key and start of value.
        delimiter: Substring used to separate end of value to next key.

    Returns:
        The extracted value of a given key, or None if not found.

    Examples:
        >>> extract_value(data_string="test=123,", key="test")
        '123'
        >>> extract_value(data_string="test=123", key="test")
        '123'
        >>> extract_value(data_string="tes=123", key="test")
        >>> extract_value(data_string="a=1,b=2,c=3", key="b")
        '2'
        >>> extract_value( \
                data_string="a>1&b>2&c>3", key="b", definer=">", delimiter="&" \
            )
        '2'
    """
    definition = f"{key}{definer}"
    start_index = data_string.find(definition)
    if start_index == -1:
        return None

    # Extract the substring starting after the key + definer.
    start_index += len(definition)
    end_index = data_string.find(delimiter, start_index)

    # Return up to the delimiter or the rest of the string if no delimiter.
    return (
        data_string[start_index:end_index]
        if end_index != -1
        else data_string[start_index:]
    )
