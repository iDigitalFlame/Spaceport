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
-- ## WirePlumber Bluetooth Configuration
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

bluez_monitor.enabled = true
bluez_monitor.properties = {
    ["with-logind"] = true,

    ["bluez5.roles"] = "[ a2dp_sink a2dp_source hfp_hf hfp_ag hsp_hs hsp_ag bap_sink bap_source ]",
    ["bluez5.headset-roles"] = "[ hfp_hf hfp_ag hsp_hs hsp_ag]",

    ["bluez5.codecs"] = "[ sbc sbc_xq aac ldac aptx aptx_hd aptx_ll aptx_ll_duplex faststream faststream_duplex ]",

    ["bluez5.hfphsp-backend"] = "native",
    ["bluez5.hfphsp-backend-native-modem"] = "none",

    ["bluez5.default.rate"] = 48000,
    ["bluez5.default.channels"] = 2,

    ["bluez5.enable-msbc"] = true,
    ["bluez5.enable-sbc-xq"] = true,
    ["bluez5.enable-hw-volume"] = true,

    ["bluez5.dummy-avrcp-player"] = true,
}
bluez_monitor.rules = {
    {
        matches = {
            {
                { "device.name", "matches", "bluez_card.*" },
            },
        },
        apply_properties = {
            ["device.profile"] = "a2dp-sink",

            ["bluez5.hw-volume"] = "[ a2dp_sink a2dp_source hfp_hf hfp_ag hsp_hs hsp_ag ]",
            ["bluez5.auto-connect"] = "[ a2dp_sink a2dp_source hfp_hf hfp_ag hsp_hs hsp_ag ]",

            ["bluez5.a2dp.ldac.quality"] = "hq",
            ["bluez5.a2dp.aac.bitratemode"] = 0,
        },
    },
    {
        matches = {
            {
                { "node.name", "matches", "bluez_input.*" },
            },
            {
                { "node.name", "matches", "bluez_output.*" },
            },
        },
        apply_properties = {
            ["bluez5.media-source-role"] = "input",
        },
    },
}
