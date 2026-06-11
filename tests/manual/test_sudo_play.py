import os
import subprocess
import pwd

def play_audio(wav_path):
    if os.geteuid() == 0:
        sudo_user = os.environ.get("SUDO_USER")
        if sudo_user:
            try:
                user_info = pwd.getpwnam(sudo_user)
                uid = user_info.pw_uid
                env = os.environ.copy()
                env["XDG_RUNTIME_DIR"] = f"/run/user/{uid}"
                # Try pw-play via sudo -u
                print(f"Running as root, delegating to {sudo_user}")
                cmd = ["sudo", "-u", sudo_user, "env", f"XDG_RUNTIME_DIR=/run/user/{uid}", "pw-play", wav_path]
                res = subprocess.run(cmd, capture_output=True)
                print(res.returncode, res.stderr)
            except Exception as e:
                print(e)
    else:
        print("Not running as root.")

play_audio('test.wav')
