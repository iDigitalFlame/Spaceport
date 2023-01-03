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

stream_defaults = {}
stream_defaults.enabled = true
stream_defaults.properties = {
  ["restore-props"] = true,
  ["restore-target"] = true,
}
stream_defaults.rules = {
  -- Rules to override settings per node
  -- {
  --   matches = {
  --     {
  --       { "application.name", "matches", "pw-play" },
  --     },
  --   },
  --   apply_properties = {
  --     ["state.restore-props"] = false,
  --     ["state.restore-target"] = false,
  --   },
  -- },
}

function stream_defaults.enable()
  if not stream_defaults.enabled then
    return
  end

  -- Save and restore stream-specific properties
  load_script("restore-stream.lua", {
    properties = stream_defaults.properties,
    rules = stream_defaults.rules,
  })
end
