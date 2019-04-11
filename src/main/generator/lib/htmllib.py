# list from https://www.lifewire.com/html-singleton-tags-3468620
singletons = {"area", "base", "br", "col", "command", "embed", "hr", "img", "input", "keygen", "link", "meta", "param", "source", "track", "wbr"}

class HTMLObject:
    def __init__(self, type, contents, options):
        self.type = type
        self.contents = list(contents)
        if "cls" in options:
            options["class"] = options["cls"]
            del options["cls"]
        if "contents" in options:
            if isinstance(options["contents"], list):
                for item in options["contents"]:
                    self.contents.append(item)
            else:
                self.contents.append(options["contents"])
            del options["contents"]
        self.options = options

    def __str__(self):
        options = ""
        for opt in self.options:
            options += ' {}="{}"'.format(opt, self.options[opt])
        contents = "".join(map(str, self.contents))
        if self.type in singletons and contents == "":
            return "<{}{}/>".format(self.type, options)
        return "<{}{}>{}</{}>".format(self.type, options, contents, self.type)

class HTML:
    def __getattr__(self, attr):
        return lambda *a, **b: HTMLObject(attr, a, b)

class UIElement:
    html = None
    def __str__(self):
        return str(self.html)

def html_encode(m: str) -> str:
    return m.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

h = HTML()

head  = h.head
body  = h.body
div   = h.div
a     = h.a
h1    = h.h1
h2    = h.h2
h3    = h.h3
p     = h.p
