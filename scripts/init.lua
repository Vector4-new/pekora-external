-- PlayerlistModule's bytecode is replaced with this
-- This is run in the CoreScript state, not the regular LocalScript state

-- there is no ref written until it actually has a reason to keep the state safe
-- so we create a signal so it is actually left alive
local dummy = game.Changed:Connect(function() end)

-- now we just wait in a loop until we know our identity has been set
while true do
    if pcall(Instance.new, "Player") then
        break
    end
end

return {
    SetVisibility = function() end,
    HideTemp = function() end
}