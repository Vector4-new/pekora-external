-- PlayerlistModule's bytecode is replaced with this
-- This is run in the CoreScript state, not the regular LocalScript state

print("This is PlayerlistModule")

return {
    SetVisibility = function() end,
    HideTemp = function() end
}