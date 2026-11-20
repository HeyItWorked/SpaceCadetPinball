// SpaceCadetPinball.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include "pch.h"

#include "winmain.h"

int MainActual(LPCSTR lpCmdLine)
{
	// Todo: get rid of restart to change resolution.
	int returnCode;
	do
	{
		returnCode = winmain::WinMain(lpCmdLine);
	}
	while (winmain::RestartRequested());
	return returnCode;
}

#ifdef _SDL_webOS_h
#include <fcntl.h>
#include <unistd.h>

// A TV has no console: stdout and stderr lead nowhere, and a start that fails leaves no trace.
// Send both to SpaceCadetPinball.log in the settings folder (on the TV, the installed app folder),
// or in /tmp when that folder is not writable. The file starts afresh on every launch.
static void RedirectOutputToLogFile()
{
	std::string folders[2];
	if (auto prefPath = SDL_GetPrefPath(nullptr, "SpaceCadetPinball"))
	{
		folders[0] = prefPath;
		SDL_free(prefPath);
	}
	folders[1] = "/tmp/";

	for (auto& folder : folders)
	{
		if (folder.empty())
			continue;
		auto file = open((folder + "SpaceCadetPinball.log").c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0644);
		if (file < 0)
			continue;

		dup2(file, STDOUT_FILENO);
		dup2(file, STDERR_FILENO);
		if (file > STDERR_FILENO)
			close(file);
		// Line buffered, so that what was printed before a crash is in the file
		setvbuf(stdout, nullptr, _IOLBF, 0);
		return;
	}
}
#endif

int main(int argc, char* argv[])
{
	std::string cmdLine;
	for (int i = 1; i < argc; i++)
		cmdLine += argv[i];

#ifdef _SDL_webOS_h
	RedirectOutputToLogFile();
	printf("Space Cadet Pinball, launch parameters: %s\n", cmdLine.c_str());
#endif
	return MainActual(cmdLine.c_str());
}

#if _WIN32
#include <windows.h>

// Windows subsystem main
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nShowCmd)
{
	return MainActual(lpCmdLine);
}

// fopen to _wfopen adapter, for UTF-8 paths
FILE* fopenu(const char* path, const char* opt)
{
	wchar_t* wideArgs[2]{};
	for (auto& arg : wideArgs)
	{
		auto src = wideArgs[0] ? opt : path;
		auto length = MultiByteToWideChar(CP_UTF8, 0, src, -1, nullptr, 0);
		arg = new wchar_t[length];
		MultiByteToWideChar(CP_UTF8, 0, src, -1, arg, length);
	}

	auto fileHandle = _wfopen(wideArgs[0], wideArgs[1]);
	for (auto arg : wideArgs)
		delete[] arg;

	return fileHandle;
}
#endif

// Run program: Ctrl + F5 or Debug > Start Without Debugging menu
// Debug program: F5 or Debug > Start Debugging menu

// Tips for Getting Started: 
//   1. Use the Solution Explorer window to add/manage files
//   2. Use the Team Explorer window to connect to source control
//   3. Use the Output window to see build output and other messages
//   4. Use the Error List window to view errors
//   5. Go to Project > Add New Item to create new code files, or Project > Add Existing Item to add existing code files to the project
//   6. In the future, to open this project again, go to File > Open > Project and select the .sln file
