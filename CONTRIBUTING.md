# Contributing

This repository is the webOS TV port. Bugs in the game logic itself belong upstream, at
[k4zmu2a/SpaceCadetPinball](https://github.com/k4zmu2a/SpaceCadetPinball); bugs in how it
behaves on a TV belong here.

## Reporting a problem

Say which TV model and webOS version, which IPK (the commit it was built from), and attach
`SpaceCadetPinball.log` from the installed app folder. The README explains where that is.
The log starts with the SDL version the TV provided, which answers most first questions.

## How a change gets built

Nobody needs the toolchain to contribute. Every push and every pull request runs
[`.github/workflows/build.yml`](.github/workflows/build.yml), which:

1. installs LG's CLI (`@webos-tools/cli`) for `ares-package`;
2. restores or downloads the webOS NDK (`1.0.g-rev.4`, about 1.2 GB, cached between runs);
3. configures with `-DWEBOS=ON` and the NDK's CMake toolchain file;
4. builds the `SpaceCadetPinball` target, then `webos-package`, which stages the app folder
   in `bin/` and runs `ares-package` on it;
5. unpacks the resulting IPK and fails unless it holds `appinfo.json` and the executable;
6. uploads the IPK and `webosbrew.manifest.json` as the `SpaceCadetPinball-ipk` artifact.

A green run means the code compiles for the TV and the package is well formed. It does not
mean the game was started: nothing in CI runs it. Say in the pull request what you tried on
a TV, and on which one.

## Things the build depends on

- The NDK ships CMake older than 3.12 and GCC 6.2, and the project is built as C++11.
  `cmake -S/-B` and `cmake --build --parallel` do not exist there.
- The app links against the SDL2 that is installed on the TV, not one from the package.
  The NDK's headers describe SDL 2.0.5, so newer SDL functions are not available.
- Code that only makes sense on a TV is guarded with `#ifdef _SDL_webOS_h`, which the NDK's
  `SDL.h` defines. Desktop builds must keep behaving like upstream.
- The game data is not in this repository. Staging downloads it; see the README.
- `webos/gamecontrollerdb.txt` is a snapshot. Refresh it with
  `sh webos/gen_gamecontrollerdb.sh update <commit>` and commit the result.
