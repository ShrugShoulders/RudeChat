#!/usr/bin/env python3
"""Helpers for validating IRC nicknames before they are stored or coloured."""
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

def is_valid_nickname(nickname):
    # Check if the nickname contains any invalid characters
    """Check whether a nickname is acceptable for the colour table.

        Rejects names that contain a space, comma, ``*``, ``?``, ``!`` or ``.``,
        or that start with ``$``, ``:``, ``#`` or ``&``. An empty string raises
        ``IndexError``.

        Args:
            nickname: The nickname to check.

        Returns:
            True if the nickname passes every check, otherwise False.
    """
    if re.search(r"[ ,*?!]", nickname):
        return False

    # Check if the nickname starts with any invalid characters
    if nickname[0] in {'$', ':'}:
        return False

    # Check if the nickname starts with channel type
    if nickname[0] in {'#', '&'}:
        return False

    # Check if the nickname contains a dot character
    if '.' in nickname:
        return False

    return True

def clean_nicknames(nicknames):
    # Return the cleaned nickname colors dictionary
    """Remove invalid nicknames from a nickname-to-colour mapping.

        Args:
            nicknames: Mapping of nickname to colour.

        Returns:
            A new dict that keeps only the entries whose nickname passes
            ``is_valid_nickname``. The input is not modified.
    """
    return {nickname: color for nickname, color in nicknames.items() if is_valid_nickname(nickname)}