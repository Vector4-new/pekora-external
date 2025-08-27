-- PlayerlistModule's bytecode is replaced with this
-- This is run in the CoreScript state, not the regular LocalScript state
-- this script should NEVER yield BEFORE OR INSIDE the while true loop

-- should be more than enough. external will use this for storing bytecode temporarily and sending us results
-- info will be sent to external with StringValue and ObjectValue
local buffer = string.rep("\0", 8 * 1024 * 1024)

-- there is no ref written until it actually has a reason to keep the state safe
-- so we create a signal so it is actually left alive
local dummy = game.Changed:Connect(function() end)

Instance.new("ModuleScript", script).Name = "dummymodule"

-- now we just wait in a loop until we know our identity has been set
while true do
    local c = buffer:sub(1, 1)

    if c == "\1" then
        break
    end
end

spawn(function()
    while wait() do
        print(pcall(require, script.dummymodule))
    end
end)

return {
    SetVisibility = function() end,
    HideTemp = function() end,

    -- prevents gc
    __buffer = buffer
}