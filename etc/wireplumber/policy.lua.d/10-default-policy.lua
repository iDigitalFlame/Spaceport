-- Wireplumber Configuration File
--
-- System Management Daemon
--
-- Copyright (C) 2016 - 2022 iDigitalFlame
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

default_policy = {}
default_policy.enabled = true
default_policy.properties = {}
default_policy.endpoints = {}
default_policy.policy = {
  ["move"] = true,
  ["follow"] = true,
  ["duck.level"] = 0.3,
  ["audio.no-dsp"] = false,
  ["filter.forward-format"] = false,
}

bluetooth_policy = {}
bluetooth_policy.policy = {
  ["use-persistent-storage"] = true,
  ["media-role.use-headset-profile"] = true,
  ["media-role.applications"] = { "Firefox", "Chromium input", "Google Chrome input", "Telegram Desktop", "telegram-desktop" },
}

function default_policy.enable()
  if not default_policy.enabled then
    return
  end
  load_module("si-node")
  load_module("si-audio-adapter")
  load_module("si-standard-link")
  load_module("si-audio-endpoint")
  load_module("default-nodes-api")
  load_module("mixer-api")
  load_script("static-endpoints.lua", default_policy.endpoints)
  load_script("create-item.lua", default_policy.policy)
  load_script("policy-node.lua", default_policy.policy)
  load_script("policy-endpoint-client.lua", default_policy.policy)
  load_script("policy-endpoint-client-links.lua", default_policy.policy)
  load_script("policy-endpoint-device.lua", default_policy.policy)
  load_script("policy-bluetooth.lua", bluetooth_policy.policy)
end
