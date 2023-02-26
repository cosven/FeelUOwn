from prompt_toolkit.utils import get_cwidth

_ELLIPSIS = '…'
_SPACE = ' '


def right_elide_or_fill_text(text, width):
    if width == 0:
        return ''

    end = pos = len(text)
    while get_cwidth(text[:pos]) > width:
        end = pos
        pos //= 2

    elided = pos != len(text)

    if elided:
        while end > pos + 1:
            mid = (pos + end) // 2
            if get_cwidth(text[:mid]) <= width:
                pos = mid
            else:
                end = mid

        if pos <= 0:
            return _ELLIPSIS

    cwidth = get_cwidth(text[:pos])
    if elided:
        if width == cwidth:
            return text[:pos-1] + get_cwidth(text[pos-1]) * _ELLIPSIS
        return text[:pos] + (width-cwidth) * _ELLIPSIS
    return text[:pos] + (width - cwidth) * _SPACE
