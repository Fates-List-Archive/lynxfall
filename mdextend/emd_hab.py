# Extra parsing for markdown (Highlighting and alert boxes)

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

# Base Control class
class Control():
    def start(self, s):
        return s
    def inner(self, s):
        return s
    def end(self, s):
        return s

# Highlight control class
class HighlightControl(Control):
    def inner(self, s):
        """At inner, add highlight followed by the text followed by ending span tag"""
        return "<span class='highlight'>" + s + "</span>"

# Box comtrol class (alert/info/error/etc. boxes)
class BoxControl(Control):
    def inner(self, s):
        style = s.split("\n")[0].strip().replace("<br />", "") # Gets the box style This controls info, alert, danger, warning, error etc...
        if style == "info": # info box
            style_class = "alert-info white"
            icon_class = "fa-solid:icon-circle"
        else: 
            return s
        return f"<div class='{style_class}' style='color: white !important;'><span class='iconify white' data-icon='{icon_class}' aria-hidden='true' data-inline='false'></span><span class='bold'>{style.title()}</span>" + s.replace(style, "", 1) + "</div>"

# This adds the == highlighter and ::: boxes
def emd(txt: str) -> str:
    # == highlighting
    ret_text = parse(txt, "==", HighlightControl())
    # ::: boxes
    ret_text = parse(ret_text, ":::", BoxControl())
    return ret_text


# Test cases

#emd.emd("Hi ==Highlight== We love you == meow == What about you? == mew == ::: info\nHellow world:::")
