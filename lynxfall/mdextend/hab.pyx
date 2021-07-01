# Extra parsing for markdown (Highlighting and alert boxes)

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
