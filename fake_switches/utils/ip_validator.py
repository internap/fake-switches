def valid_ip_v4(address):
    parts = address.split(".")
    for item in parts:
        if not item.isdigit() or not 0 <= int(item) <= 255:
            raise InvalidIpError
    if len(parts) != 4:
        raise IncompleteIpError
    return True


class InvalidIpError(Exception):
    pass


class IncompleteIpError(Exception):
    pass
