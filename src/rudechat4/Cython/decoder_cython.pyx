# decoder_cython.pyx
# cython: language_level=3
from cpython.unicode cimport PyUnicode_FromStringAndSize

def decode_text(bytes text):
    """
    Decodes IRC text and returns list of tuples:
    (string, bold, italic, underline, strikethrough, inverse, fg, bg)
    """
    cdef Py_ssize_t i = 0, n = len(text)
    cdef unsigned char c  # unsigned avoids negative bytes
    cdef list output = []
    cdef int bold=0, italic=0, underline=0, strikethrough=0, inverse=0, fg=0, bg=1
    cdef list buffer = []  # collect byte values safely
    cdef int tmp
    cdef list num_buf

    while i < n:
        c = text[i]
        if c == 2:  # \x02 bold
            if buffer:
                segment = bytes(buffer).decode('utf-8', 'ignore')
                output.append((segment, bold, italic, underline, strikethrough, inverse, fg, bg))
                buffer = []
            bold ^= 1
        elif c == 0x1D:  # \x1D italic
            if buffer:
                segment = bytes(buffer).decode('utf-8', 'ignore')
                output.append((segment, bold, italic, underline, strikethrough, inverse, fg, bg))
                buffer = []
            italic ^= 1
        elif c == 0x1F:  # \x1F underline
            if buffer:
                segment = bytes(buffer).decode('utf-8', 'ignore')
                output.append((segment, bold, italic, underline, strikethrough, inverse, fg, bg))
                buffer = []
            underline ^= 1
        elif c == 0x1E:  # \x1E strikethrough
            if buffer:
                segment = bytes(buffer).decode('utf-8', 'ignore')
                output.append((segment, bold, italic, underline, strikethrough, inverse, fg, bg))
                buffer = []
            strikethrough ^= 1
        elif c == 0x16:  # \x16 inverse
            if buffer:
                segment = bytes(buffer).decode('utf-8', 'ignore')
                output.append((segment, bold, italic, underline, strikethrough, inverse, fg, bg))
                buffer = []
            tmp = fg
            fg = bg
            bg = tmp
        elif c == 3:  # \x03 color
            if buffer:
                segment = bytes(buffer).decode('utf-8', 'ignore')
                output.append((segment, bold, italic, underline, strikethrough, inverse, fg, bg))
                buffer = []
            i += 1
            num_buf = []
            # parse foreground digits
            while i < n and text[i] >= ord('0') and text[i] <= ord('9') and len(num_buf) < 2:
                num_buf.append(chr(text[i]))
                i += 1
            if num_buf:
                try:
                    fg = int("".join(num_buf))
                except ValueError:
                    fg = 0
            if i < n and text[i] == ord(','):
                i += 1
                num_buf = []
                while i < n and text[i] >= ord('0') and text[i] <= ord('9') and len(num_buf) < 2:
                    num_buf.append(chr(text[i]))
                    i += 1
                if num_buf:
                    try:
                        bg = int("".join(num_buf))
                    except ValueError:
                        bg = 1
            i -= 1  # compensate for outer loop increment
        elif c == 0x0F:  # \x0F reset
            if buffer:
                segment = bytes(buffer).decode('utf-8', 'ignore')
                output.append((segment, bold, italic, underline, strikethrough, inverse, fg, bg))
                buffer = []
            bold=italic=underline=strikethrough=inverse=0
            fg=0
            bg=1
        else:
            buffer.append(c)  # safe: c is unsigned 0-255
        i += 1

    if buffer:
        segment = bytes(buffer).decode('utf-8', 'ignore')
        output.append((segment, bold, italic, underline, strikethrough, inverse, fg, bg))
    return output
