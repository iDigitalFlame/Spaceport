# The Spaceport Project

Management of my personal ArchLinux notebook (Spaceport).
Contains management and system configuration files that keep the system running smoothly.

The "config" directory conatins all the seperate configuration files, which are symlinked into the appropiate directories.

The "lib", "libexec" and "bin" directories contain the source for the Spaceport System Management Daemon (SMD).  The SMD is used to manage and control the various power and management utilities.
The daemon may be controlled using the "powerctl" python script.

The files contained here are mainly for backup, but are able to be used in any system or downloaded to learn more about the internal workings of an ArchLinux system or just for the management daemon source.

### TODO
- Add a SHA256 file checker to check /boot to confirm secure boot.
- Add a notification pass through to user from the root level daemon.