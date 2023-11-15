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
    {
        matches = {
            {
                { "node.name", "matches", "alsa_input.*" },
            },
            {
                { "node.name", "matches", "alsa_output.*" },
            },
        },
        apply_properties = {
        },
    },
    {
        matches = {
            {
                { "node.name", "matches", "alsa_output.*" },
                { "node.description", "equals", "USB Audio" },
            },
            {
                { "node.name", "matches", "alsa_output.*" },
                { "node.description", "matches", "USB Audio (*)" },
            },
            {
                { "node.name", "matches", "alsa_output.*" },
                { "node.description", "matches", "Built-in Audio (*)" },
            },
        },
        apply_properties = {
            ["priority.session"] = 800,
        },
    },
    {
        matches = {
            {
                { "node.name", "matches", "alsa_input.*" },
                { "node.description", "equals", "USB Audio" },
            },
            {
                { "node.name", "matches", "alsa_input.*" },
                { "node.description", "matches", "USB Audio (*)" },
            },
            {
                { "node.name", "matches", "alsa_input.*" },
                { "node.description", "matches", "Built-in Audio (*)" },
            },
        },
        apply_properties = {
            ["priority.session"] = 1800,
        },
    },
    {
        matches = {
            {
                { "node.name", "equals", "alsa_input.pci-0000_00_1f.3.capture.0.0" },
            },
        },
        apply_properties = {
            ["priority.session"] = 1900,
        },
    },
    {
        matches = {
            {
                { "node.name", "equals", "alsa_output.pci-0000_00_1f.3.playback.0.0" },
            },
        },
        apply_properties = {
            ["priority.session"] = 900,
        },
    },
    {
        matches = {
            {
                { "node.name", "matches", "bluez_input.*" },
            },
        },
        apply_properties = {
            ["priority.session"] = 2100,
        },
    },
    {
        matches = {
            {
                { "node.name", "matches", "bluez_output.*" },
            },
        },
        apply_properties = {
            ["priority.session"] = 1100,
        },
    },
}
