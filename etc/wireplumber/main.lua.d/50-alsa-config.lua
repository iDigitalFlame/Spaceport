-- ################################
-- ### iDigitalFlame  2016-2024 ###
-- #                              #
-- #            -/`               #
-- #            -yy-   :/`        #
-- #         ./-shho`:so`         #
-- #    .:- /syhhhh//hhs` `-`     #
-- #   :ys-:shhhhhhshhhh.:o- `    #
-- #   /yhsoshhhhhhhhhhhyho`:/.   #
-- #   `:yhyshhhhhhhhhhhhhh+hd:   #
-- #     :yssyhhhhhyhhhhhhhhdd:   #
-- #    .:.oyshhhyyyhhhhhhddd:    #
-- #    :o+hhhhhyssyhhdddmmd-     #
-- #     .+yhhhhyssshdmmddo.      #
-- #       `///yyysshd++`         #
-- #                              #
-- ########## SPACEPORT ###########
-- ### Spaceport + SMD
-- ## WirePlumber Main Configuration
--
-- Copyright (C) 2016 - 2024 iDigitalFlame
--
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with this program.  If not, see <https://www.gnu.org/licenses/>.
--

alsa_monitor.enabled = true
alsa_monitor.properties = {
    ["alsa.midi"] = false,
    ["alsa.reserve"] = true,
    ["alsa.jack-device"] = false,
    ["alsa.reserve.priority"] = -20,
    ["alsa.midi.monitoring"] = false,
    ["alsa.reserve.application-name"] = "WirePlumber",
}
alsa_monitor.rules = {
    {
        matches = {
            {
                { "device.name", "matches", "alsa_card.*" },
            },
        },
        apply_properties = {
            ["api.alsa.use-acp"] = false,
            ["api.alsa.use-ucm"] = true,
            ["api.acp.auto-port"] = false,
            ["api.alsa.ignore-dB"] = false,
            ["api.alsa.soft-mixer"] = false,
            ["api.acp.auto-profile"] = false,
        },
    },
    -- Outputs
    {
        -- Match HDMI/PCI Outputs
        -- They have the lowest priority
        matches = {
            {
                { "node.name", "matches", "alsa_output.pci-*" },
                { "node.description", "matches", "Built-in Audio (*)" },
                { "node.nick", "not-equals", "ALC3254 Analog" },
            },
        },
        apply_properties = {
            ["priority.session"] = 800,
        },
    },
    {
        -- Match Built-in Speakers
        -- They have the second-lowest priority
        matches = {
            {
                { "node.name", "matches", "alsa_output.pci-*" },
                { "node.nick", "equals", "ALC3254 Analog" },
            },
        },
        apply_properties = {
            ["priority.session"] = 850,
            ["node.description"] = "Internal Speakers"
        },
    },
    {
        -- Match Built-in Headphone Jack(s) (Including Docks)
        -- Set as the default device with the third-lowest priority
        matches = {
            {
                { "node.name", "matches", "alsa_output.usb-Generic_USB_*" },
                { "node.description", "equals", "USB Audio" },
            },
            {
                { "node.name", "matches", "alsa_output.usb-Generic_USB_*" },
                { "node.description", "matches", "USB Audio (*)" },
            },
        },
        apply_properties = {
            ["priority.session"] = 875,
            ["node.description"] = "Headphone Jack"
        },
    },
    {
        -- Match USB Outputs
        -- They have the second-highest priority
        matches = {
            {
                { "node.name", "matches", "alsa_output.usb-*" },
                { "node.description", "not-equals", "Headphone Jack" },
            },
        },
        apply_properties = {
            ["priority.session"] = 900,
        },
    },
    {
        -- Match Bluetooth Outputs
        -- They have the highest priority
        matches = {
            {
                { "node.name", "matches", "bluez_output.*" },
            },
        },
        apply_properties = {
            ["priority.session"] = 1100,
        },
    },
    -- Inputs
    {
        -- Match Built-in Microphone
        -- This has the lowest priority and is disabled by default
        matches = {
            {
                { "node.name", "matches", "alsa_input.pci-*" },
                { "node.nick", "equals", "ALC3254 Analog" },
            },
        },
        apply_properties = {
            ["device.disabled"] = true,
            ["priority.session"] = 1800,
            ["node.description"] = "Internal Microphone"
        },
    },
    {
        -- Match Built-in Headphone Jack(s) (Including Docks)
        -- Set as the default device with the second-lowest priority
        matches = {
            {
                { "node.name", "matches", "alsa_input.usb-Generic_*" },
                { "node.description", "equals", "USB Audio" },
            },
            {
                { "node.name", "matches", "alsa_input.usb-Generic_*" },
                { "node.description", "matches", "USB Audio (*)" },
            },
        },
        apply_properties = {
            ["priority.session"] = 1850,
            ["node.description"] = "Headphone Jack"
        },
    },
    {
        -- Match USB Audio Inputs
        -- They have the second-highest priority
        matches = {
            {
                { "node.name", "matches", "alsa_input.usb-*" },
                { "node.description", "not-equals", "Headphone Jack" },
            },
        },
        apply_properties = {
            ["priority.session"] = 1875,
        },
    },
    {
        -- Match Bluetooth Inputs
        -- They have the highest priority
        matches = {
            {
                { "node.name", "matches", "bluez_input.*" },
            },
        },
        apply_properties = {
            ["priority.session"] = 1900,
        },
    },
    {
        -- Fix Razor Headsets to Appear as Headsets
        matches = {
            {
                { "api.alsa.card.components", "equals", "USB1532:054e" },
            },
        },
        apply_properties = {
            ["api.alsa.card.id"] = "Headset",
        },
    },
}
