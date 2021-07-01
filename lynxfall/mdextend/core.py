from .emd_hab import HighlightControl, BoxControl


# This adds the == highlighter and ::: boxes
def emd(txt):
    # == highlighting
    ret_text = parse(txt, "==", HighlightControl())
    # ::: boxes
    ret_text = parse(ret_text, ":::", BoxControl())
    return ret_text
