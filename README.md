# TimeshiftCockpit (TSC)

Timeshifts Overview shows all active timeshift services.
![Screenshot](pic1.jpg)

Configuration menu allows the preset of up to 2 permanent timeshift services.
![Screenshot](pic2.jpg)

## Features
TimeshiftCockpit is a plugin for Open Enigma2 receivers that provides advanced timeshift functionality:

- on demand timeshift (only timeshifts when manually started and stopped)
- permanent timeshift
	- variable permanent timeshift (always timeshifts current channel)
	- fixed permanent timeshift (of up to 2 fixed services)
- record every timeshift event (pressing the REC key)

## Usage
- PLAY/PAUSE to start on demand timeshift or playback of permanent timeshift
- On demand timeshift: STOP to exit timeshift playback and stop timeshift recording
- Permanent timeshift: STOP/EXIT to exit timeshift playback but continue with timeshift recording
- Cursor LEFT/RIGHT for fast forward/backward
- Cursor UP/DOWN to enter channel selection list
- CHANNEL/BOUQUET up/down for intelligent jump
- TAB left/right for previous/next event
- Permanent timeshift: MENU to display a choice list of events for playback
- REC to record any event contained in timeshift. If the event is the last one in timeshift and incomplete, timeshift will continue until the event is complete. If power off is pressed before recording is complete, recording will continue in idle mode.
- YELLOW shows a list of timeshift recording jobs
- BLUE shows a list of active timeshifts

## Conflicts
- TSC may conflict with other permanent timeshift plugins, so remove those before installing TimeshiftCockpit

## Limitations
- Tested on OpenViX and OpenATV with DM900.

## Links
- Installation: https://OpenCockpit.github.io/TimeshiftCockpit
