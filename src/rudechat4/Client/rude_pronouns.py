#!/usr/bin/env python3
"""Optional gender-neutral rewriting of chat text.

    Text is only changed in channels listed (one per line, case-insensitive)
    in ``filtered_channels.txt`` in the config folder. URLs are never
    modified. The channel list is cached and re-read when the file's
    modification time changes.
"""
from rudechat4.shared_imports import *
from rudechat4.global_variables import *
import os, re

_URL_RE = re.compile(r'(https?://\S+)')
_cache = {'mtime': None, 'channels': frozenset()}

def _filtered_channels(path):
"""Return the set of channel names that should be rewritten.

    Args:
        path: Path to ``filtered_channels.txt``.

    Returns:
        A frozenset of lower-cased channel names, empty if the file is
        missing or unreadable.
"""
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return frozenset()
    if mtime != _cache['mtime']:
        with open(path) as f:
            _cache['channels'] = frozenset(l.strip().lower() for l in f if l.strip())
        _cache['mtime'] = mtime
    return _cache['channels']

def _match_case(src, repl):
"""Copy the capitalisation style of ``src`` onto ``repl``.

    All-caps stays all-caps, a leading capital stays capitalised, anything
    else is returned unchanged.
"""
    if len(src) > 1 and src.isupper():
        return repl.upper()
    if src[0].isupper():
        return repl[0].upper() + repl[1:]
    return repl

# Nouns that change after a possessive: "his husband" -> "their spouse"
_NOUN_SWAPS = {
    'husband': 'spouse', 'wife': 'spouse', 'son': 'child', 'daughter': 'child',
    'brother': 'sibling', 'sister': 'sibling',
    'boyfriend': 'partner', 'girlfriend': 'partner',
}
_NOUN_RE = re.compile(r'\b(his|her)\s+(%s)\b' % '|'.join(_NOUN_SWAPS), re.I)

# Verb agreement after he/she
_IRREGULAR = {'is': 'are', 'was': 'were', 'has': 'have', 'does': 'do', 'goes': 'go',
              "isn't": "aren't", "wasn't": "weren't", "hasn't": "haven't",
              "doesn't": "don't"}
_NOT_VERBS = {'always', 'sometimes', 'perhaps', 'as', 'this', 'thus', 'us', 'yes',
              'less', 'across', 'unless', 'towards', 'besides', 'his', 'its'}
_ADV = r"(?:(?:always|never|usually|often|just|also|still|really|rarely)\s+)?"
_SUBJ_VERB_RE = re.compile(r"\b(he|she)\s+(" + _ADV + r")([a-z]+(?:'t)?)\b", re.I)
_HAVE_RE = re.compile(r"\b(he|she)'s(?=\s+(?:been|got|had|gone|done|made|seen|never)\b)", re.I)

def _conjugate(verb):
"""Convert a third-person singular verb to its plural form.

    Handles irregular verbs such as ``is`` and ``has`` and common endings
    like ``-ies`` and ``-es``. Words that only look like verbs (``always``,
    ``unless`` and similar) are returned unchanged.
"""
    v = verb.lower()
    if v in _IRREGULAR:
        return _IRREGULAR[v]
    if v in _NOT_VERBS or len(v) < 3 or not v.endswith('s') or v.endswith('ss'):
        return verb
    if v.endswith('ies'):
        return verb[:-3] + 'y'
    if re.search(r'(ss|sh|ch|x|z|o)es$', v):
        return verb[:-2]
    return verb[:-1]

def _subj_verb(m):
"""Regex callback: replace ``he/she`` plus a verb with ``they`` plus the plural verb."""
    return _match_case(m.group(1), 'they') + ' ' + m.group(2) + _conjugate(m.group(3))

# "her" is an object ("I saw her") before these, otherwise possessive ("her book")
_OBJECT_NEXT = (r'(?=\s*(?:$|[.,!?;:)]|(?:to|for|with|at|on|in|about|from|and|or|but|'
                r'that|if|when|because|as|so|too|again|out|up|down|back|away|off|over|'
                r'by|into|of|a|an|the|some|this|these|those|yesterday|today|now)\b))')
_HER_OBJ_RE = re.compile(r'\bher\b' + _OBJECT_NEXT, re.I)

_SIMPLE = [
    (r"he's|she's", "they're"), (r"he'll|she'll", "they'll"), (r"he'd|she'd", "they'd"),
    (r'himself|herself', 'themself'), (r'hers', 'theirs'),
    (r'him', 'them'), (r'his|her', 'their'), (r'he|she', 'they'),
    (r'guys|gals|lads|lasses', 'folks'),
]
_SIMPLE_RE = re.compile(r'\b(%s)\b' % '|'.join(p for p, _ in _SIMPLE), re.I)
_SIMPLE_MAP = {alt: rep for pat, rep in _SIMPLE for alt in pat.split('|')}

def _simple(m):
"""Regex callback: swap a single pronoun using the lookup table, keeping its case."""
    return _match_case(m.group(0), _SIMPLE_MAP[m.group(0).lower()])

def _neutralize(text):
"""Apply every pronoun rule to one piece of text, in order.

    Order matters: possessive-plus-noun pairs, ``he's/she's`` contractions,
    subject-verb agreement, object ``her``, then the simple word swaps.
"""
    text = _NOUN_RE.sub(lambda m: 'their ' + _NOUN_SWAPS[m.group(2).lower()], text)
    text = _HAVE_RE.sub(lambda m: _match_case(m.group(1), 'they') + "'ve", text)
    text = _SUBJ_VERB_RE.sub(_subj_verb, text)
    text = _HER_OBJ_RE.sub(lambda m: _match_case(m.group(0), 'them'), text)
    return _SIMPLE_RE.sub(_simple, text)

def replace_pronouns(text, channel=None):
"""Rewrite gendered pronouns in a message when the channel opts in.

    Args:
        text: The message text.
        channel: The channel the message belongs to. If it is empty or not
            listed in ``filtered_channels.txt``, the text is returned as is.

    Returns:
        The rewritten text. URLs inside the text are left untouched.
"""
    path = os.path.join(G_CONFIG_DIR, 'filtered_channels.txt')
    if not channel or channel.lower() not in _filtered_channels(path):
        return text
    parts = _URL_RE.split(text)  # odd indexes are URLs: leave alone
    return ''.join(p if i % 2 else _neutralize(p) for i, p in enumerate(parts))