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

v4l2_monitor.enabled = true
v4l2_monitor.rules = {
  {
    matches = {
      {
        { "device.name", "matches", "v4l2_device.*" },
      },
    },
    apply_properties = {
    },
  },
  {
    matches = {
      {
        { "node.name", "matches", "v4l2_input.*" },
      },
      {
        { "node.name", "matches", "v4l2_output.*" },
      },
    },
    apply_properties = {
    },
  },
}
