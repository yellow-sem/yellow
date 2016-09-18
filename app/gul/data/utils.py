from requests.cookies import RequestsCookieJar, create_cookie


def data_from_cookiejar(cookiejar):
    """Transform a cookiejar into serializable data."""

    data = []

    for cookie in cookiejar:

        attrs = {
            'domain': cookie.domain,
            'path': cookie.path,
            'port': cookie.port,
            'name': cookie.name,
            'value': cookie.value,
            'rfc2109': cookie.rfc2109,
            'secure': cookie.secure,
            'version': cookie.version,
        }

        data.append(attrs)

    return data


def cookiejar_from_data(data):
    """Obtain a cookiejar from serializable data."""

    cookiejar = RequestsCookieJar()

    for attrs in data:
        cookie = create_cookie(**attrs)
        cookiejar.set_cookie(cookie)

    return cookiejar
