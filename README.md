# Todo
- [x] Complete / Has base function
- [ ] Needs to be done / all child goals need to be completed

**RudeChat4.2.0: (2/3 - $66.67%)**
- [x] Fix messages loading in the wrong order
- [x] Fix nickname highlighting (use ANSI escape codes?)
- [ ] Implement updated GUI

**RudeChat4 (Carry-overs): (1/3 - $33.33%)**
- [ ] Small Bugfixes
	- [ ] Make clicking on the app reopen the window (MacOS)
	- [x] tested all core functions and fixed minor bugs
- [ ] OS Builds

# RudeChat IRC Client: For Fun & Reasons. (Req Python 3.13+)
## How to Install
### Windows (Installer)
Download the installer. Windows installs to `%LOCALAPPDATA%\Programs\RudeChat4`.
### Linux (Binary/.deb)
- Linux Stand Alone tar file. 
	- Update .desktop file to the executable path. 
- Deb package available for Debian based sysems. 

### Linux (Build from Source)
- Clone the repo.
- CD to the cloned directory and use the below command to install RudeChat. 

```sh
pip install -r requirements.txt .
```
- use `rudechat`.

### MacOS (.app)

- Download the zip file, unzip.
- Move .app file to applications. 
- You may have to authorize its use as the .app is yet to be signed.

### MacOS (Build from Source)

- Clone the repo.

- CD to the cloned directory and use the below command to download RudeChat's requirements.


```sh
pip3 install -r requirements.txt
```

- Use the below command to build the MacOS App.

```sh
python3 setup.py py2app
```

- If the command finishes with `Done!`, you'll find your Mac App in the `dist` folder. If not, [tell us we messed up.](https://github.com/ShrugShoulders/RudeChat/issues)

## Cool Tips

It is suggested that you use: https://github.com/source-foundry/Hack as your font.

Right click anywhere to open and edit the config.

RudeChat assumes server_name.rudeserver is available and configed properly:

For assistance find me on irc.libera.chat/#rudechat

![alt text](https://i.imgur.com/N9AqHKx.png)
