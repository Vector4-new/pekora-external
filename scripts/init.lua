-- PlayerlistModule's bytecode is replaced with this
-- This is run in the CoreScript state, not the regular LocalScript state
-- this script should NEVER yield BEFORE OR INSIDE the while true loop

-- there is no ref written until it actually has a reason to keep the state safe
-- so we create a signal so it is actually left alive
local dummy = game.Changed:Connect(function() end)

-- should be more than enough. external will use this for everything
local buffer = string.rep("\0", 8 * 1024 * 1024)

-- now we just wait in a loop until we know our identity has been set
while true do
    if buffer:sub(0, 1) ~= "\0" then
        break
    end
end

return {
    SetVisibility = function() end,
    HideTemp = function() end,

    -- prevents gc
    __buffer = buffer
}