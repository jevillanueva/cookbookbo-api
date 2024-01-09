from starlette.datastructures import URL
def validateHTTPS(url: URL, schema: str = ""):
    if schema == "":
        return url
    else:
        if schema == "https":
            url = url.replace(scheme="https")
        return url
