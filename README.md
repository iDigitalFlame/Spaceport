# The Spaceport System Management Daemon (SMD)

This is the configuration for my personal Archlinux notebook, dubbed "spaceport".

This repository includes many files used in the configuration of the operating system and
other installed packages. (Listed in packages.md)

The System Management Daemon (SMD) is a system that allows for management of many system-level components.
Including brightness, networking, bluetooth, wireless, sleep, cpu and virtual machines.
SMD is located in usr/lib and can be invoked from the bin and usr/lib/libexec directories.

## Required Packages (Arch Specific)

- dash
- dnsmasq
- edk2-ovmf
- flatery-icon-theme-git
- git
- git-lfs
- gnome-keyring
- imagemagick
- iproute2
- iptables-nft
- kora-icon-theme
- logrotate
- openssl
- pacman-contrib
- pipewire
- pipewire-pulse
- python
- python-gobject
- qemu-audio-pipewire
- qemu-audio-spice
- qemu-base
- qemu-chardev-spice
- qemu-hw-display-qxl
- qemu-hw-display-virtio-gpu
- qemu-hw-display-virtio-gpu-pci
- qemu-hw-display-virtio-vga
- qemu-hw-usb-host
- qemu-hw-usb-redirect
- qemu-vhost-user-gpu
- rsync
- samba
- sbsigntools
- spice-gtk
- sudo
- swaybg
- swayfx (or sway)
- swayidle
- swtpm
- tar
- vimix-cursors
- waybar
- wireplumber

## Recommended Packages

- blueman
- bluez
- libsecret
- NetworkManager
- network-manager-applet
- yay

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Z8Z4121TDS)

### Hydra Secureboot Config

There's not a package that contains a secureboot image that contains pre-enrolled
keys, so that'll have to be a manual install.

To do this, we'll follow [this](https://wiki.archlinux.org/title/QEMU#Enabling_Secure_Boot)
guide on the ArchLinux Wiki.

Download the file [here](http://archive.ubuntu.com/ubuntu/pool/main/e/edk2/ovmf_2024.02-2_all.deb)
and extract it to get the `OVMF_VARS_4M.ms.fd` file, which can then be copied to
`/usr/share/edk2/x64/OVMF_VARS.ms.4m.fd` to get the pre-enrolled image.

You can also just copy that over your VM specific `bios.vars` file (defaults to
`uefi_vars.fd` in the VM folder) if you want it VM specific.
