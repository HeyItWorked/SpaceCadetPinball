# Space Cadet Pinball for LG webOS TVs

The pinball table that came with Windows XP, running natively on an LG TV and played with
the remote that is already on your couch. Left and Right are the flippers, OK launches the
ball, Back opens the menu. No keyboard, no pointer, no pairing.

![The Space Cadet table with the ball waiting at the plunger and "Awaiting Deployment" on the display](Screenshots/screenshot-1.jpg)

*The table as the desktop build of this code draws it. The TV shows the same picture at
full height with black bars left and right. There is no capture from a TV: the set refuses
screen capture.*

This is a fork of [webosbrew/SpaceCadetPinball](https://github.com/webosbrew/SpaceCadetPinball),
mariotaku's webOS port of [k4zmu2a/SpaceCadetPinball](https://github.com/k4zmu2a/SpaceCadetPinball),
the decompilation of the original game. What this fork adds is a build that works again,
controls for a TV remote, and a log file for when it does not start.

## Playing

| Remote | What it does |
| --- | --- |
| Left, Right | Left and right flipper |
| OK or Down | Plunger. Hold to pull back, release to launch |
| Up | Bump the table from below |
| Back | Pause and open the menu. Back again closes it and play continues |
| OK after "OK Starts New Game" | Start the next game |

Back never quits. The menu it opens has Resume, New Game, Select Players (1 to 4), Sound,
Music, High Scores, Player Controls and, last, Exit. Move with the arrows, choose with OK.

If the game is paused and no menu is open (a dialog leaves it that way), the display says
"Game Paused, Back to Continue", and Back does that.

The Exit key of the remote is not taken by the game; the system keeps it.

A USB keyboard or a gamepad also works:

| | Keyboard | Gamepad |
| --- | --- | --- |
| Flippers | `Z` and `/`, or Left and Right | Left and right shoulder |
| Plunger | Return or Down | A |
| Bump table left, right | `X` and `.` | D-pad left and right |
| Bump table from below | Up | D-pad up |
| Menu | | Start |
| New game, pause | `F2`, `F3` | through the menu |
| Sound, music, controls | `F5`, `F6`, `F8` | through the menu |

Bumping the table sideways has no key on the remote. Player Controls in the menu lets you
give each action up to three keys of your own; choose a slot, then press the key.

When you beat a high score the game asks for a name. Without a keyboard, move to Ok with
the arrows and take the suggested "Player 1".

## Installing

You need a TV that accepts developer apps. The route below is the one that was used on an
LG OLED B4 with webOS 24 (9.2.2), rooted, with SSH from Homebrew Channel. `lgtv` is an SSH
host alias for root on the TV.

Get the IPK from the `SpaceCadetPinball-ipk` artifact of the latest
[Build webOS IPK](../../actions/workflows/build.yml) run, then copy it over:

```sh
ssh lgtv 'cat > /media/developer/temp/pinball.ipk' < com.github.k4zmu2a.space-cadet-pinball_2.0.100_arm.ipk
```

`scp` does not work with the SSH server on that set, hence the pipe. Then, on the TV:

```sh
script -qc "luna-send -w 90000 -n 1 -f luna://com.webos.appInstallService/dev/install '{\"id\":\"com.github.k4zmu2a.space-cadet-pinball\",\"ipkUrl\":\"/media/developer/temp/pinball.ipk\",\"subscribe\":true}'" /dev/null
```

It answers `{ "subscribed": true, "returnValue": true }`. Two things that cost time:

- `script -qc "..." /dev/null` is not decoration. Without a terminal, `luna-send` on this
  firmware reports success and installs nothing.
- `ipkUrl` is a path on the TV. An `http` address does not work.

It should now be in the TV's app list. From the shell it starts with:

```sh
script -qc "luna-send -w 8000 -n 1 -f luna://com.webos.applicationManager/launch '{\"id\":\"com.github.k4zmu2a.space-cadet-pinball\"}'" /dev/null
```

`ares-install` from LG's CLI should do the same job on a TV in Developer Mode. It has not
been tried with this package.

## Building

### Let CI do it

Every push builds the IPK on GitHub Actions; nothing needs to be installed locally.
[CONTRIBUTING.md](CONTRIBUTING.md) lists what the workflow does, step by step.

### Locally

This needs x86-64 Linux, because that is what the NDK is built for, plus `wget`, `unzip`
and Python 3.8 or newer. The commands are the workflow's own, with the last step swapped
for the packager in `tools/`, so LG's CLI is not needed:

```sh
# once: the webOS NDK, about 1.2 GB, installs to /opt/webos-sdk-x86_64/1.0.g
curl -fsSL https://github.com/webosbrew/meta-lg-webos-ndk/releases/download/1.0.g-rev.4/webos-sdk-x86_64-armv7a-neon-toolchain-1.0.g.sh -o ndk.sh
chmod 755 ndk.sh && sudo ./ndk.sh -y

# every build
. /opt/webos-sdk-x86_64/1.0.g/environment-setup-armv7a-neon-webos-linux-gnueabi
mkdir -p build && (cd build && cmake .. \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DWEBOS=ON \
    -DCMAKE_TOOLCHAIN_FILE=/opt/webos-sdk-x86_64/1.0.g/sysroots/x86_64-webossdk-linux/usr/share/cmake/OEToolchainConfig.cmake)
cmake --build build --target SpaceCadetPinball -- -j"$(nproc)"
cmake --build build --target webos-ipk
```

The IPK lands in the repository root. `webos-ipk` first runs `webos-stage`, which fills
`bin/` with everything the app folder needs, and then packs that folder with
`tools/build_ipk.py`, whose usage is `build_ipk.py <app-dir> [out-dir]`.

Given the folder unpacked from a CI-built IPK, `build_ipk.py` produces a package with the
same file list and identical contents. Neither such a package nor the `webos-ipk` target
has been through CI or onto a TV; the CI artifact, built with `ares-package`, is the one
that has.

### Game data

The repository contains no game data. Staging downloads `PinballXP.zip` from archive.org
and unpacks it into `bin/data`, so every IPK carries the original game's files. They are
Microsoft's and Cinematronics', and the MIT licence of this code does not cover them.

## Gamepads

The package ships `gamecontrollerdb.txt`, made from `webos/gamecontrollerdb.txt`: the
Linux section of [SDL_GameControllerDB](https://github.com/mdqinc/SDL_GameControllerDB) at
commit `4e87e3c`, 752 mappings.

What was checked is the file, not a pad. The wired Xbox 360 controller
(`030000005e0400008e02000014010000`, line 707) is in it and maps every button the default
bindings use. So are the USB ids of the Xbox One and Series pads, the DualShock 4 and the
DualSense. No controller has been plugged into the TV.

If yours does nothing, the log names it, with the GUID SDL gave it and whether a mapping
matched. A missing GUID is one line to add to `webos/gamecontrollerdb.txt`.

## When it does not start

The game writes `SpaceCadetPinball.log` next to its settings, which on the TV is the
installed app folder:

```sh
ssh lgtv 'cat /media/developer/apps/usr/palm/applications/com.github.k4zmu2a.space-cadet-pinball/SpaceCadetPinball.log'
```

If that folder is not writable the log goes to `/tmp/SpaceCadetPinball.log`. It starts
afresh on every launch and opens with the SDL version, platform name and video driver the
TV provided, then says where the game data was found, how many controller mappings loaded,
and why sound or music are off if they are.

Settings, key bindings and high scores live in `imgui_pb.ini` in the same folder. Deleting
that file puts everything back to defaults.

## Honest limits

- **One TV.** Installing, launching and the picture were confirmed on an LG OLED B4,
  webOS 24 (9.2.2), with the build before the remote controls existed.
- **The remote controls, the menu, the log file and the gamepad handling have not been
  run on a TV.** They were written against the SDL headers of the NDK and the source of
  webosbrew's SDL fork, with no TV at hand. Whether Back reaches the game on this
  firmware is the first thing to check. The flippers, the plunger and "OK Starts New
  Game" do not depend on it, and the log shows which SDL the TV has.
- **Memory use has not been measured.** The TV it ran on has 1.7 GB.
- **Music is off by default** and the game data's track is MIDI. Whether the TV's
  SDL_mixer can play it is unknown; the log says so if the track cannot be loaded.
- **Removing the app** over SSH has no tested command. `dev/uninstall` does not exist on
  this firmware.
- **Updating** over an installed copy may keep the old `imgui_pb.ini`. Old key bindings
  are replaced by the remote defaults once; other settings stay.

## Where things are

| Path | What |
| --- | --- |
| `SpaceCadetPinball/` | The game. TV-only code is inside `#ifdef _SDL_webOS_h` |
| `SpaceCadetPinball/options.cpp` | Default key bindings (`Options.KeyDft`) and settings |
| `SpaceCadetPinball/winmain.cpp` | Start-up, the remote menu, event handling |
| `webos/` | App manifest, icon, splash, bundled `libstdc++`, controller mappings |
| `tools/build_ipk.py` | Packager that needs no LG tooling |
| `.github/workflows/build.yml` | The CI build |
| `Platform/Linux/BUILD.md` | Building the desktop version, as upstream describes it |

## Credits

Andrey Muzychenko decompiled the game and made it portable; mariotaku brought it to webOS.
The code is under the [MIT licence](LICENSE). The game itself belongs to its owners.
