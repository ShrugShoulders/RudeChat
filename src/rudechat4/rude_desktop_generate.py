import os
import platform

def create_desktop_file():
    match platform.system():
        case "Linux":
            home_dir = os.path.expanduser("~")
            desktop_file_path = os.path.join(home_dir, "Desktop/RudeChat4.desktop")

            if os.path.exists(desktop_file_path):
                return

            desktop_entry = f"""[Desktop Entry]
            Type=Application
            Name=RudeChat4
            Comment=A cross-platform PyQt6 IRC chat app
            Exec=env QT_QPA_PLATFORM=xcb rudechat
            Icon={home_dir}/.config/rudechat/rude_icon_roundedge.png
            Terminal=false
            Categories=Network;Chat;
            """

            os.makedirs(os.path.dirname(desktop_file_path), exist_ok=True)

            with open(desktop_file_path, "w") as f:
                f.write(desktop_entry)

            os.chmod(desktop_file_path, 0o755)
            print(f"Desktop file created at: {desktop_file_path}")