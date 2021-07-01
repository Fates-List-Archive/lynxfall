from .emd_hab import HighlightControl, BoxControl

def parse(rtxt, look, control):
    txtl = rtxt.split(look) # Turn the text into a string split based on the markdown character we are looking for
    i, j = 0, 0 # i goes through the list, j is the current state
    ret_text = "" # The result text
    while i < len(txtl):
        if j == 0:
            # This is the start before the specified tag, add it normally
            ret_text += control.start(txtl[i]) # Pre tag
            j+=1
        elif j == 1:
            # This is the text we actually want to parse
            ret_text += control.inner(txtl[i]) # Inner text
            j+=1
        else:
            ret_text += control.end(txtl[i]) # After tag
            j = 1
        i+=1
    return ret_text

# This adds the == highlighter and ::: boxes
def emd(txt):
    # == highlighting
    ret_text = parse(txt, "==", HighlightControl())
    # ::: boxes
    ret_text = parse(ret_text, ":::", BoxControl())
    return ret_text

# Test cases

#emd.emd("Hi ==Highlight== We love you == meow == What about you? == mew == ::: info\nHellow world:::")
