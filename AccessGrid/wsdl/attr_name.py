
def modify(name):
    if name.startswith("_"):
        return name[1:]
    else:
        return name
