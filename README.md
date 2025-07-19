# IL-2-Great-Battles-Rank-Promotion-Mod  
* A Python utility for IL-2 Sturmovik: Battle of Stalingrad that:
	* Monitors your career database in real time for new missions.
	* Auto-promotes pilots based on configurable performance thresholds.
        * Promotions are granted if pilots meet PCP, OR sortie count combined with a failure rate thresholds for their current rank.
		* Chance-based logic applies to the player pilot: even if criteria are met, a promotion is only awarded based on a randomized probability, which decreases slightly at higher ranks.
        * After a failed promotion attempt, the player must wait a configurable number of in-game days (cooldown) before the next attempt is evaluated.
        * If the player fails to promote after a configurable number of consecutive attempts, a forced promotion is granted automatically.
        * AI pilots get promoted based on thresholds (no chance-based approach)	
	* Displays in-game pop-ups featuring promotion ceremonies.
	* Generates personalized PNG certificates (German, US, Soviet, and British styles) and a png of the complete promotion ceremony for each promotion a player earned. Pictures are saved in the game's "Career" folder 
 	* Tested with game version 5.506b	

⸻

# Features  

* Real-time monitoring of the cp.db career database, restarting automatically whenever IL-2 closes and reopens.
* Configurable thresholds for Player Combat Performance PCP), sorties, failure rate per rank, promotion cooldown days, and forced promotion (after x failed promotion attempts).
* Localization support: choose your UI language; Soviet ranks always display in Cyrillic.
* Authentic-style certificates:
* German & US certificates modeled on historical originals.
* Fictional (but polished) Soviet and British versions.
* Lightweight GUI powered by Tkinter; pop-ups auto-close after 20 seconds (remaining time is displayed).
* PyInstaller ready: includes `rank_promotion_checker_new10_AI.spec` for one-file bundling.

# Requirements  

*	Python 3.8+
*	Dependencies (install via pip):
```bash
pip install -r requirements.txt
```
⸻

# Installation  

To install and deploy the Rank Promotion Mod via Inno Setup, follow these steps:

### 1. Build the EXE  
1. Ensure all Python source files, fonts, ceremony templates, and helper scripts live at the same folder level (no extra subdirectories).  
a. *Optional:* You can modify the `ceremony_XX.png` to your liking. Just save it again with the exact name it had before.

2. Generate the standalone executable using the included spec file:
```bash
pyinstaller rank_promotion_checker_new10_AI.spec
```
3. After completion, locate the exe. Navigate to the folder where you downloaded and extracted all .py files and assets from the repository:
```bash
<folder of all py and asset files>/dist/rank_promotion_checker.exe
```


### 2. Prepare the Inno Setup Package  
1.	Download IL-2 Rank Mod Inno Setup.zip from this repository.
2.	Unzip the archive into a folder (e.g. IL-2 Rank Mod Inno Setup).
3.	Copy your previously built executable (rank_promotion_checker.exe) into the `bin` subfolder of that folder.
4.	If you don’t already have it, install Inno Setup:
https://jrsoftware.org/isinfo.php

### 3. Compile the Installer  
1.	Open Rank_Mod6.iss in the Inno Setup Compiler.
2.	Click Compile (F9).
3.	The installer will package your pre-built rank_promotion_checker.exe (which already includes all ceremony images, certificate templates, and font files) along with the necessary scripts and assets.

### 4. Run the Installer  

* Double-click the generated setup executable.
* Follow the prompts to select minimum & maximum ranks for each country and choose optional medal/emblem styles.

### 5. First Launch & Configuration  

On first run, promotion_config.json is created in your game’s data/Career folder. Open it to tweak your thresholds:
```bash
	{
	  "game_path": "...",
	  "language": "ENG",
	  "max_ranks": { "101": 5 (up to 13), "102": 5 (up to 13), "103": 5 (up to 13), "201": 5 (up to 13) },
	  "thresholds": [
	    [pcp, sortie_count, max_failure_rate],
	    …
	  ]
	"PROMOTION_COOLDOWN_DAYS": x (0-100),
	"PROMOTION_FAIL_THRESHOLD": y (0-100)
	}
```
* `pcp` = Player Combat Performance required for auto-promotion **OR**  
*	`sortie_count = number of missions flown` in conjunction with
	    `max_failure_rate = (total sorties – successful sorties) ÷ total sorties` for auto-promotion

### 6. Change Settings  

Re-run the installer whenever you want new parameters. It will detect and uninstall the previous version—your pilot progress remains intact—then prompt you for updated preferences.

### 7. Auto-start (optional)  

Place a shortcut to rank_promotion_checker.exe in:
```bash
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```
On Windows login, the checker launches automatically, waits for il-2.exe, and begins monitoring your cp.db and executes promotions (beyond the hard-coded 5-rank in-game limit)  when eligible.

# Pre-compiled Installer (optional)  
If you do not wish to compile the executable yourself (and go through all the hassle above), you can download the pre-built Inno Setup installer here:  
https://drive.google.com/file/d/1No74iYiLEAkYa9FB7EIWLTXcb8sNnUxa/view?usp=sharing  
Unzip, and run `IL2_Rank_Mod_Installer.exe` and follow the installation instructions (Steps 4.-7. of the previous paragraph)

See [LICENSE.md](./LICENSE.md) for details on project and font licensing.

# Project Structure  
```bash
IL-2-Great-Battles-Rank-Promotion-Mod/
├── certificates.py                      # Certificate-generation routines
├── config.py                            # Resource paths & config loader/saver
├── helpers.py                           # Utility functions (font loader, process check)
├── logger.py                            # Debug logging with rotation
├── promotion.py                         # DB monitor and promotion logic
├── ranks.py                             # Rank-name lookup from locale files
├── ui.py                                # Tkinter pop-up display logic
├── popup_render.py                      # Tkinter save promotion pop-up to png 
├── rank_promotion_checker_new10_AI.py   # Main entry point
├── rank_promotion_checker_new10_AI.spec # PyInstaller spec for one-file EXE
├── IL-2 Rank Mod Inno Setup.zip         # Inno Setup package (unzip and compile)
├── certificate_template.png             # Blank template for German certificates
├── Ceremony_DE.png                      # German ceremony image
├── Ceremony_GB.png                      # British ceremony image
├── Ceremony_RU.png                      # Soviet ceremony image
├── Ceremony_US.png                      # US ceremony image
├── IBMPlexSans-Light.ttf                # Custom font used by UI
├── DejaVuSans.ttf                       # Fallback font for Western scripts
├── Kyiv Machine.ttf                     # Cyrillic font for Russian text
├── NotoSansSC-Regular.otf               # Chinese font for CJK support
├── SpecialElite.ttf                     # Decorative font for Latin text
├── rank.ico                             # Application icon
├── promotion_certificate_GB.png         # Blank template for British certificate
├── Promotion_certificate_RU.png         # Blank template for Soviet certificate
├── Promotion_certificate_US.png         # Blank template for US certificates
├── requirements.txt                     # Necessary Python packages
├── LICENSE.md	                         # License info 
└── README.md                            # This file
