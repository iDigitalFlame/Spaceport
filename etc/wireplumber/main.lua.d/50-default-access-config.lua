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

default_access.enabled = true
default_access.properties = {
  ["enable-flatpak-portal"] = false,
}
default_access.rules = {
  {
    matches = {
      {
        { "media.category", "=", "Manager" },
      },
    },
    default_permissions = "all",
  },
  {
    matches = {
      {
        { "pipewire.access", "=", "restricted" },
      },
    },
    default_permissions = "rx",
  },
}