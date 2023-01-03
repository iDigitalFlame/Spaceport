-- Wireplumber Configuration File
--
-- System Management Daemon
--
-- Copyright (C) 2016 - 2023 iDigitalFlame
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
  ["with-logind"] = false,
  ["bluez5.enable-msbc"] = true,
  ["bluez5.enable-sbc-xq"] = true,
  ["bluez5.enable-hw-volume"] = true,
  ["bluez5.hfphsp-backend"] = "native",
  ["bluez5.dummy-avrcp-player"] = false,
  ["bluez5.headset-roles"] = "[ hsp_hs hsp_ag hfp_hf hfp_ag ]",
  ["bluez5.codecs"] = "[ sbc sbc_xq aac ldac aptx aptx_hd aptx_ll aptx_ll_duplex faststream faststream_duplex ]",
}
bluez_monitor.rules = {
  {
    matches = {
      {
        { "device.name", "matches", "bluez_card.*" },
      },
    },
    apply_properties = {
      -- Available values: a2dp-sink (default), headset-head-unit
      ["device.profile"] = "a2dp-sink",
      ["bluez5.a2dp.aac.bitratemode"] = 0,
      ["bluez5.a2dp.ldac.quality"] = "auto",
      ["bluez5.hw-volume"] = "[ hfp_hf hsp_hs a2dp_sink hfp_ag hsp_ag a2dp_source ]",
      ["bluez5.auto-connect"] = "[ hfp_hf hsp_hs a2dp_sink hfp_ag hsp_ag a2dp_source ]",
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
    },
  },
}
