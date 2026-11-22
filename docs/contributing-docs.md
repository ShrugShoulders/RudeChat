# Documenting code

## Docstring style

Use Google-style docstrings. Keep type hints in signatures, not in the docstring text.

```python
def clean_nicknames(nicknames):
    """Drop entries whose nickname isn't valid on IRC.

    Args:
        nicknames: Mapping of nickname to colour.

    Returns:
        A new dict with only the valid nicknames.
    """
```

Rules of thumb:

- First line is a short sentence in the imperative mood, ending with a period.
- Say what the code does and why it exists. Don't repeat the function name.
- Document side effects: GUI updates, files written, tasks scheduled, network traffic.
- Mark coroutines clearly, since callers must `await` them or wrap them in `create_task`.
- Describe arguments only when the name and type don't make them obvious.
- Add comments for non-obvious logic. Don't comment what the line already says.

## Per-module checklist

1. A module docstring at the top, placed after the shebang and before the imports. Say what the module is for and name the main class or functions.
2. A class docstring for every class, including what state it owns.
3. A docstring for every public method and function. Skip trivial private helpers unless the behavior is surprising.
4. Update the module's row in [modules.md](modules.md).
5. If the module adds user-visible behavior, update [commands.md](commands.md) or [data-files.md](data-files.md).

## Rules for changes

- Documentation changes must not change behavior. Keep docstring commits separate from code changes.
