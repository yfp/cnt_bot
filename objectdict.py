class ObjectDict(dict):
    def __init__(self, dict_input):
        for k,v in dict_input.items():
            if isinstance(v,dict):
                v = ObjectDict(v)
            self[k] = v

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)