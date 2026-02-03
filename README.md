# CHIP-8-Emulator
My lightweight CHIP-8 emulator created with pygame and tkinter which has support for per game profiles as well as automatically categorising ROMs by type due to folder structures and favourites stored locally in a database using sqlite3.
Contains all CHIP-8 features with binary 64x32 display, simple buzz audio (diable optional) as well as the CHIP-8 keypad mapped to the top left of the keyboard

#----Key Features----#
Library manager which automatically scans the /ROMS directory and supports subfolders if you wanted games to be categorised by genre/ROM type etc. 
Per game profiles where you can assign specific settings to individual ROMs such as the games' clock speed, colour scheme, muted audio as well as some extra features like a CRT ghosting effect as well as a rainbow FG colour mode.
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

#----Screenshots----#
Profile manager window:
<img width="348" height="578" alt="image" src="https://github.com/user-attachments/assets/9336c6d5-5081-43f0-b12a-7c1da77cd673" />

CHIP-8 library window:
<img width="447" height="647" alt="image" src="https://github.com/user-attachments/assets/ea1b1ea5-12f5-4b36-811c-72b971620735" />

Example games running:
<img width="761" height="408" alt="image" src="https://github.com/user-attachments/assets/116f5a47-d013-42e0-82b9-dd884ec2b7d7" />

<img width="767" height="409" alt="image" src="https://github.com/user-attachments/assets/284e756e-5e33-4d6e-af42-48c317483b75" />
