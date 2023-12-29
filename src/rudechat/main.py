#!/usr/bin/env python3

from .rudegui import RudeGUI
from .initialize_clients import initialize_clients

import asyncio
from tkinter import Tk


def main():
    root = Tk()
    app = RudeGUI(root)

    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)

    loop = asyncio.get_event_loop()
    loop.create_task(initialize_clients(app))

    def tk_update():
        try:
            loop.stop()
            loop.run_forever()
        finally:
            loop.stop()
            root.after(100, tk_update)

        root.after(100, tk_update)


if __name__ == '__main__':
    main()
