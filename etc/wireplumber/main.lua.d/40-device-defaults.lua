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

device_defaults = {}
device_defaults.enabled = true
device_defaults.properties = {
  ["auto-echo-cancel"] = true,
  ["use-persistent-storage"] = true,
  ["echo-cancel-sink-name"] = "echo-cancel-sink",
  ["echo-cancel-source-name"] = "echo-cancel-source",
}
device_defaults.persistent_profiles = {
  {
    matches = {
      {
        -- Matches all devices
        { "device.name", "matches", "*" },
      },
    },
    profile_names = {
      "off",
      "pro-audio"
    }
  },
}

function device_defaults.enable()
  if not device_defaults.enabled then
    return
  end

  load_module("default-nodes", device_defaults.properties)
  load_script("policy-device-profile.lua", {
    persistent = device_defaults.persistent_profiles
  })

  load_script("policy-device-routes.lua", device_defaults.properties)

  if device_defaults.properties["use-persistent-storage"] then
    load_module("default-profile")
  end
end
