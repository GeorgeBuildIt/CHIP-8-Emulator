# CHIP-8-Emulator
My lightweight CHIP-8 emulator created with pygame and tkinter which has support for per game profiles as well as automatically categorising ROMs by type due to folder structures and favourites stored locally in a database using sqlite3.

#----Key Features----#
Library manager which automatically scans the /ROMS directory and supports subfolders if you wanted games to be categorised by genre/ROM type etc. 
Per game profiles where you can assign specific settings to individual ROMs such as the games' clock speed, colour scheme as well as some extra features like a CRT ghosting effect as well as a rainbow FG colour mode.
SQLite3 Backend which uses a local database (settings.db) to store the aforementioned per game profiles as well as favourite ROMs which will appear at the top of the library where a link table between roms and profiles is also used so that games specific profiles will be saved.
Hotkeys:
Ctrl + R (reset rom)
Ctrl + S (create quicksave)
Ctrl + L (load quicksave)
Ctrl + P (pause rom)

CHIP-8 Control scheme:

<img width="143" height="84" alt="image" src="https://github.com/user-attachments/assets/093d7dba-1262-4ae9-a670-b1e9eab7bb42" />

(keyboard -> chip-8 keypad)

#----Techincal Aspects----#
Python with pygame for the CHIP-8 game loading and tkinter for the library UI, sqlite3 for the database implementation. Uses pyinstaller to package the exe file which will auto create a /ROMS directory and settings.db file.
