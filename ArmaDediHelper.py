#   Arma Dedi Helper, a self-contained tool to easily create -
#   dedicated server configuration files for the 'Arma' series of games.
#   Copyright (c) 2024 Tuomas Iso-Heiko
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
#
#   1.  This software is only to be used with 'Arma' servers that comply with
#       the rules defined by 'Bohemia Interactive a.s'.
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.

"""
ArmaDediHelper is a tool to quickly create local dedicated servers for Arma 3.
"""

import sys
import os
import glob
import shutil
import platform
from html.parser import HTMLParser
import urllib.request

# Version number
# format: Major, Minor, Patch
VERSION_NUMBER = "0.2.0"

# To-do list:
# 1. Make a docs page available through GitHub pages that details how to use this program

# Gracefully exit program, informing the user.
def exit_program(reason):
    """
    Graceful program exit wrapper
    """
    print(f"\nExiting... Reason: {reason}")
    sys.exit(0)

# Verify that the execution environment is ok, executable present etc...
def verify_execution_location():
    """
    Checks that we are in the correct location (Arma 3 Root).

    It verifies this by looking for arma3server_x64
    """
    # The first print has a newline to make reading in terminal easier
    print("\nLooking for Arma 3 Server...")
    found_64bit = False

    # Search with wildcard because Linux servers don't have extension
    if glob.glob("arma3server_x64*"):
        found_64bit = True
        print("Found Arma 3 Server (64bit)")
    else:
        print("Error: Could not find the 64 bit server!"
              "\nMake sure your installation is correct.")

    return found_64bit

# Search for ServerProfiles directory, return bool depending on found / created or not.
def find_serverprofiles_dir():
    """
    Checks if ./ServerProfiles/ exists.
    If it doesn't ask the user if they want to make it
    """
    # The first print has a newline to make reading in terminal easier
    print("\nLooking for ServerProfiles directory...")

    # First check - if not found, ask user if we want to create
    if not os.path.isdir('ServerProfiles'):
        print("Error: Could not find ServerProfiles directory."
              "\nDo you wish to create one now?")
        create_serverProfiles_prompt = input("Y / n: ") or "Y"
        if create_serverProfiles_prompt == "Y":
            try:
                os.mkdir("ServerProfiles")
            except Exception as error:
                print("Error while creating ServerProfiles directory: ", error)
                return False

    # Second check, actual return of the function.
    # Will take into account if mkdir fails
    if os.path.isdir('ServerProfiles'):
        print("ServerProfiles directory found!")
        return True
    else:
        print("Error: Could not find ServerProfiles directory!")
        return False

# Search for the 'basic configuration files' we'll use for all profiles later on.
def find_base_configuration():
    """
    Verifies that the base configuration (base_basic.cfg and base_server.cfg) exist.
    Also informs the user of the checks.
    """
    # The first print has a newline to make reading in terminal easier
    print("\nLooking for base configs in ServerProfiles...")

    verify_default_configs()

    found_base_server = False
    if os.path.isfile('ServerProfiles\\base_server.cfg'):
        print("Found base base_server.cfg!")
        found_base_server = True
    else:
        print("Error: Could not find base_server.cfg!"
              "\nPlease create base_server.cfg in the ServerProfiles directory.")

    found_base_basic = False
    if os.path.isfile('ServerProfiles\\base_basic.cfg'):
        print("Found base base_basic.cfg!")
        found_base_basic = True
    else:
        print("Error: Could not find base_basic.cfg!"
              "\nPlease create base_basic.cfg in the ServerProfiles directory.")

    # Both need to exist
    return (found_base_server and found_base_basic)

# Search for mod presets exported from launcher, from the ServerProfiles directory.
def find_modpresets():
    """
    Searches ./ServerProfiles/ for A3 Launcher exported mod presets
    """
    # The first print has a newline to make reading in terminal easier
    print("\nLooking for mod presets in ServerProfiles...")

    all_found_presets = []
    for file in glob.glob("ServerProfiles/*.html"):
        try:
            with open(file, "r", -1, "utf-8-sig") as open_file:
                for line in open_file:
                    # This string should appear at least twice in the first 10 lines
                    if "Arma 3 Launcher" in line:
                        all_found_presets.append(file)
                        break
        except Exception as error:
            print("Error while searching for mod presets: ", error)
            return []

    if len(all_found_presets) == 0:
        print("Could not find any mod presets in ServerProfiles!"
              "\nMake sure you have placed the preset in the right directory."
              "\nIf you don't have a preset, export one from the Arma 3 Launcher.")
    else:
        print("Found the following presets:")
        for preset in all_found_presets:
            print(preset)
    return all_found_presets

# Ask user which preset to use
def user_prompt_preset(presets):
    """
    Asks user which preset they want to use.

    Presets are found from ./ServerProfiles/
    """
    # The first print has a newline to make reading in terminal easier
    presetname = input("\nPlease type the name of the mod preset to use: ")

    found_preset = ""
    for preset in presets:
        if presetname in preset:
            found_preset = preset
            break

    if found_preset:
        print(f"Selected preset: {found_preset}")
    else:
        print("Error: Query did not match any of the previously found presets!"
              "\nMake sure that your capitalization is correct.")

    return found_preset

# Finds a substring between two characters
# This code has been written by ChatGPT 3.5
def extract_substring(string, start_char, end_char):
    """
    Helper function to extract a substring.

    Made by ChatGPT 3.5
    """
    start_index = string.find(start_char)
    if start_index == -1:
        return None
    start_index += len(start_char)

    end_index = string.find(end_char, start_index)
    if end_index == -1:
        return None

    return string[start_index:end_index]

# Check if the files for this preset are present, if not, prompt to create them now.
def check_preset_files(preset):
    """
    Prompts the user to create the preset's directory, or what to do if it already exists
    """
    # The first print has a newline to make reading in terminal easier
    print("\nLooking for preset configuration...")
    preset_name = extract_substring(preset, "\\", ".")
    preset_path = f"ServerProfiles\\{preset_name}\\"

    if not os.path.isdir(preset_path):
        print(f"Failed to find the directory for this preset ({preset_path}).")
        create_preset_prompt = input("Would you like to create them now? (Y/n): ") or "Y"

        if create_preset_prompt.upper() == "Y":
            if not create_preset_files(preset, preset_name):
                return False # Return false if fails
    else:
        try:
            recreate_preset_prompt = input("Found the preset's directory!"
                                           " Enter the number of the action you wish to take:"
                                           "\n(Default - 1): Nothing, don't touch the files!"
                                           "\n(2): Regenerate the mod parameter"
                                           "\n(3): Regenerate everything,"
                                           " this will remove any modifications you've made!\n"
                                           ) or 1
            recreate_preset_prompt = int(recreate_preset_prompt)
        except Exception as error:
            print("Error: Failed to parse your input,"
                  f" make sure you've entered an integer!\nError: {error}")
            return False

        match recreate_preset_prompt:
            case 2:
                print("Rewriting params.txt")
                if not write_params_file(preset, preset_name):
                    return False # return false if fails
            case 3:
                print("Rewriting everything")
                if not create_preset_files(preset, preset_name):
                    return False # Return false if fails
            case _:
                print("Doing nothing ...")

    return True

def verify_default_configs() -> None:
    """
    Checks that base_basic.cfg and base_server.cfg exist.
    If they do not, they will be downloaded from the GitHub repository.
    """
    # Verify basic configuration
    if not os.path.isfile("ServerProfiles\\base_basic.cfg"):
        # Download the default one from GitHub
        with urllib.request.urlopen("https://raw.githubusercontent.com/rekterakathom/"
                                    "ArmaDediHelper/main/configs/base_basic.cfg",
                                    timeout=10) as response:
            file_path = "ServerProfiles\\base_basic.cfg"
            content = response.read()
            if response.getcode() == 200:
                with open(file_path, 'wb') as file:
                    file.write(content)
                print('basic.cfg downloaded successfully')
            else:
                print('Failed to download basic.cfg')

    # Verify server configuration
    if not os.path.isfile("ServerProfiles\\base_server.cfg"):
        # Download the default one from GitHub
        with urllib.request.urlopen("https://raw.githubusercontent.com/rekterakathom/"
                                    "ArmaDediHelper/main/configs/base_server.cfg",
                                    timeout=10) as response:
            file_path = "ServerProfiles\\base_server.cfg"
            content = response.read()
            if response.getcode() == 200:
                with open(file_path, 'wb') as file:
                    file.write(content)
                print('server.cfg downloaded successfully')
            else:
                print('Failed to download server.cfg')

# Create the preset folders and all the files in it
def create_preset_files(preset, preset_name):
    """
    Creates the files for the preset
    """
    # The first print has a newline to make reading in terminal easier
    print("\nCreating preset files...")

    # Make the directory
    if not os.path.isdir(f"ServerProfiles\\{preset_name}"):
        try:
            os.mkdir(f"ServerProfiles\\{preset_name}")
        except Exception as error:
            print("Error while creating directory for preset: ", error)
            return False

    verify_default_configs()

    # Copy over the basic configuration
    try:
        shutil.copy("ServerProfiles\\base_server.cfg", f"ServerProfiles\\{preset_name}\\server.cfg")
        shutil.copy("ServerProfiles\\base_basic.cfg", f"ServerProfiles\\{preset_name}\\basic.cfg")
    except Exception as error:
        print("Error while copying config files: ", error)
        return False

    # Create the start script
    print("\nCreating the start script...")
    if platform.system() == "Windows":
        print("Detected platform: Windows - creating batch script 'start.bat'")
        try:
            with open(f"ServerProfiles\\{preset_name}\\start.bat", "w") as startscript:
                startscript.write('start "" "..\\..\\arma3server_x64.exe"'
                                  ' -cfg="%~dp0basic.cfg"'
                                  ' -config="%~dp0server.cfg"'
                                  ' -profiles="%~dp0Profiles"'
                                  ' -port=2302'
                                  ' -par="%~dp0params.txt"')
        except Exception as error:
            print("Error while creating the batch script: ", error)
            return False

    if not write_params_file(preset, preset_name):
        return False # Return False if fails

    return True

# Fetch all the mods from the HTML document
def get_mods_from_preset(preset, preset_name):
    """
    Parses a modlist from an A3 launcher exported preset list
    """

    class PresetParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.found_mods = {}
            self.current_name = ""
            self.current_link = ""
            self.current_attribute = ""

        def handle_starttag(self, tag, attrs):
            for attr, value in attrs:
                if attr == "data-type":
                    if value == "DisplayName":
                        self.current_attribute = "DisplayName"
                        break
                    if value == "Link":
                        self.current_attribute = "Link"
                        break
                else:
                    self.current_attribute = ""

        def handle_data(self, data):
            if self.current_attribute == "DisplayName":
                self.current_name = data.strip()
            if self.current_attribute == "Link":
                self.current_link = data.strip()

        def handle_endtag(self, tag):
            if hasattr(self, 'current_name') and hasattr(self, 'current_link'):
                self.found_mods[self.current_name] = self.current_link
                del self.current_name
                del self.current_link
            self.current_attribute = ""

        def get_found_mods(self):
            return self.found_mods

    parser = PresetParser()
    try:
        with open(preset, "r", -1, "utf-8-sig") as presetfile:
            parser.feed(presetfile.read())
    except Exception as error:
        print("Error while reading the mod preset: ", error)
        return []

    mod_id_list = []
    print(f"\nFound the following mods from the preset {preset_name}:")
    for name, url in parser.get_found_mods().items():
        print(f"{name} - {url}")
        id_index = url.find("=")
        if id_index != -1:
            mod_id_list.append(url[id_index + 1:])
    return mod_id_list

def write_params_file(preset, preset_name):
    """
    Writes the params file.

    We use it only to load the mods,
    as modlists will otherwise be too long to handle without params file
    """
    print("\nBuilding mod parameter...")
    # Get modlist
    modlist = get_mods_from_preset(preset, preset_name)
    modparam = ""
    for mod in modlist:
        try:
            path = os.path.abspath(f"..\\..\\workshop\\content\\107410\\{mod}")
            modparam += (path + ";")
        except Exception as error:
            print("Error while building mod parameter: ", error)
            return False

    print("\nCreating the parameter file...")
    try:
        with open(f"ServerProfiles\\{preset_name}\\params.txt", "w", -1, "UTF-8") as paramsfile:
            paramsfile.write(f'-servermod=""\n-mod="{modparam}"')
    except Exception as error:
        print("Error while writing parameter.txt file: ", error)
        return False

    return True

def print_server_instructions():
    """
    Tell the user how to use their new server
    """
    print("\nSetup finished!")
    print("You now have the minimum required server configuration in"
          " '\\ServerProfiles\\<name-of-preset>\\'")

    print("\nIt is highly recommended that you now manually"
          " tweak the configs and the startup script to your needs.")
    print("You can find the server logs (.rpt files) to assist you in this endeavour in"
          " '\\ServerProfiles\\<name-of-preset>\\profile\\'")

    print("\nTo start the server, run the shell script located in the specified directory.")

# Entry point
def main():
    """
    Sequentially executes all necessary functions to create a dedicated server instance
    """
    print(f"\nWelcome to Arma Dedi Helper!\nVersion: {VERSION_NUMBER}")

    # Verify that this script is being executed in the server root
    if not verify_execution_location():
        exit_program("Could not find server files.")

    # Check that ServerProfiles exists, we'll need it later
    if not find_serverprofiles_dir():
        exit_program("Could not find ServerProfiles directory.")

    # Look for the base configuration files
    if not find_base_configuration():
        exit_program("Could not find base configuration files in ServerProfiles.")

    # Check that we have modpresets to use
    presets = find_modpresets()
    if len(presets) == 0:
        exit_program("Could not find any presets to use.")

    # Prompt the user for the preset they would like to use
    selected_preset = user_prompt_preset(presets)
    if not selected_preset:
        exit_program("Preset selection failed.")

    # If preset doesn't have files set up, create them
    # Always regenerate modlist if argument is passed
    if not check_preset_files(selected_preset):
        exit_program("Failed to create server files.")

    # Inform the user how to run their new server installation and exit :)
    print_server_instructions()
    exit_program("Script complete.")

# Don't run as a module
if __name__ == "__main__":
    main()
