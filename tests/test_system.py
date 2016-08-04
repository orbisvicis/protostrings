import protostrings
import pytest


###############################################################################
## testing data
###############################################################################

count_source_lazy = 0
count_source_context = 0

@protostrings.lazy_string
def ls_1():
    global count_source_lazy
    count_source_lazy += 1
    return " @@ "

@protostrings.lazy_string
def ls_2(a=22, b=33, c=44, d=None, e="word"):
    global count_source_lazy
    count_source_lazy += 1
    return " ++++ "

lsm_1 = protostrings.LazyStringMemo(ls_2)

@protostrings.context_string(l=False)
def cs_right_1(lhs, rhs):
    global count_source_context
    count_source_context += 1
    data = "word"
    if not rhs:
        raise protostrings.ContextStringValueError(data)
    if rhs[0] in ")":
        return "({}".format(data)
    else:
        return data

@protostrings.context_string(l=False)
def cs_right_2(lhs, rhs):
    global count_source_context
    count_source_context += 1
    data = "word"
    if len(rhs) <= 15:
        raise protostrings.ContextStringValueError(data)
    if rhs[:3] == "cat":
        return "({}) ".format(data)
    else:
        return data

@protostrings.context_string(r=False)
def cs_left_1(lhs, rhs):
    global count_source_context
    count_source_context += 1
    data = "third"
    if len(lhs) <= 15:
        raise protostrings.ContextStringValueError(data)
    if lhs.rstrip()[-3:] == "ing":
        return "({}) ".format(data)
    else:
        return data

@protostrings.context_string()
def cs_both_1(lhs, rhs):
    global count_source_context
    count_source_context += 1
    data = "fourth"
    if len(lhs) <= 5 or len(rhs) <= 3:
        raise protostrings.ContextStringValueError(data)
    if lhs.rstrip()[:-3] == "ing":
        return "({}) ".format(data)
    elif rhs.lstrip()[:3] == "and":
        return "[{}] ".format(data)
    else:
        return data


###############################################################################
## testing functions
###############################################################################

def count_lazy_leaves(lazy_string):
    match = lambda d:   (       isinstance(d, protostrings.LazyString)
                        and not isinstance(d, protostrings.ContextString)
                        )
    if not isinstance(lazy_string, protostrings.LazyString):
        return 0
    else:
        return sum(1 for d in lazy_string.leaves() if match(d))


###############################################################################
## tests
###############################################################################

@pytest.mark.parametrize\
        ( ( "source_type"
          , "source"
          , "target"
          )
        , [ ( protostrings.ContextString
            , (ls_1 + cs_right_1) + ls_1 + cs_right_1
            , " @@ word @@ word"
            )
          , ( protostrings.ContextString
            , (ls_1 + cs_right_1) + (ls_1 + cs_right_1)
            , " @@ word @@ word"
            )
          , ( protostrings.ContextString
            , ls_1 + cs_right_1 + cs_right_1
            , " @@ wordword"
            )
          , ( str
            , cs_right_2 + " one" + " two" + " three" + " four"
            , "word one two three four"
            )
          , ( str
            , "bazaar  " + (("calque   " + ((cs_both_1 + cs_right_2) + "  aria  ")) + "kindergarten")
            , "bazaar  calque   fourthword  aria  kindergarten"
            )
          , ( protostrings.LazyString
            , "cat " + (("dog " + (((ls_1 + cs_right_2) + cs_both_1) + " bird")) + " squirrel")
            , "cat dog  @@ wordfourth bird squirrel"
            )
          , ( str
            , cs_right_1 + ")[0], adding " + cs_left_1 + "to " + cs_both_1 + "and integrating."
            , "(word)[0], adding (third) to [fourth] and integrating."
            )
          ]
        )
def test_evaluation(source_type, source, target):
    assert type(source) is source_type
    if not isinstance(source, protostrings.LazyString):
        assert source == target
        return
    global count_source_lazy
    global count_source_context
    count_target_lazy = count_lazy_leaves(source)
    for i in range(2):
        count_source_lazy = 0
        count_source_context = 0
        assert str(source) == target
        assert count_source_lazy == count_target_lazy
    source = source.memoize()
    for i in range(2):
        count_source_lazy = 0
        count_source_context = 0
        assert str(source) == target
        if i == 0:
            assert count_source_lazy == count_target_lazy
        else:
            assert count_source_lazy == 0
            assert count_source_context == 0
