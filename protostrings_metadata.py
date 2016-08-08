import os.path


class Metadata:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def splitlinesat(string, separator):
    split = []
    group = []
    for line in string.splitlines():
        if separator in line:
            split.append("\n".join(group))
            group = []
        else:
            group.append(line)
    if group:
        split.append("\n".join(group))
    return split


root = os.path.dirname(os.path.abspath(__file__))
sphinx_index = os.path.join(root, "docs", "source", "index.rst")
with open(sphinx_index, "r") as index:
    long_description = splitlinesat(index.read(), "split here")[1]
    long_description = long_description.strip()


metadata = Metadata\
    ( name              = "protostrings"
    , version           = "1.0.0"
    , author            = "Yclept Nemo"
    , url               = "https://github.com/orbisvicis/protostrings"
    , description       = "String-like Objects"
    , long_description  = long_description
    , classifiers       = [ "Development Status :: 5 - Production/Stable"
                          , "Intended Audience :: Developers"
                          , "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)"
                          , "Operating System :: OS Independent"
                          , "Programming Language :: Python :: 3 :: Only"
                          , "Topic :: Software Development :: Libraries"
                          ]
    , license           = "GPLv3"
    )
