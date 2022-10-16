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

libcamera_monitor.enabled = false
libcamera_monitor.rules = {
  {
    matches = {
      {
        { "device.name", "matches", "libcamera_device.*" },
      },
    },
    apply_properties = {
    },
  },
  {
    matches = {
      {
        { "node.name", "matches", "libcamera_input.*" },
      },
      {
        { "node.name", "matches", "libcamera_output.*" },
      },
    },
    apply_properties = {
      ["node.pause-on-idle"] = true,
    },
  },
}