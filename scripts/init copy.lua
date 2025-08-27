-- PlayerlistModule's bytecode is replaced with this
-- This is run in the CoreScript state, not the regular LocalScript state
-- this script should NEVER yield BEFORE OR INSIDE the while true loop

-- should be more than enough. external will use this for storing bytecode temporarily and sending us results
-- info will be sent to external with StringValue and ObjectValue
local buffer = string.rep("\0", 8 * 1024 * 1024)
local bridge
local initing = true
local step1 = false


-- there is no ref written until it actually has a reason to keep the state safe
-- so we create a signal so it is actually left alive
local dummy = game.Changed:Connect(function() end)
local dummy2 = game.Changed:Connect(function() end)
local dummy3 = game.Changed:Connect(function() end)

-- now we just wait in a loop until we know our identity has been set
while true do
    local c = buffer:sub(1, 1)

    if c == "\1" then
        step1 = true

        bridge = Instance.new("Folder", game:GetService("CoreGui"))
        bridge.Name = "BridgeFolder"
    end

    if step1 then
        if c == "\2" then
            break
        end
    end
end

bridge.Parent = nil

if initing then
    local id = 0
    local refs = {}

    local function IToS(n)
        return string.char(n % 256, math.floor(n / 256) % 256, math.floor(n / 65536) % 256, math.floor(n / 16777216) % 256)
    end

    local function SToI(s)
        local b0, b1, b2, b3 = s:byte(1, 4)

        return b0 + b1 * 256 + b2 * 65536 + b3 * 16777216
    end

    function loadstring(text)
        id = id + 1

        local mod = Instance.new("ModuleScript")
        local data = Instance.new("Folder")
        local chunks = math.ceil(#text / 200000)

        data.Name = string.format("%d-%d", 0, id)

        for i = 1, chunks do
            local sv = Instance.new("StringValue", data)

            sv.Name = string.format("Source%.3d", i)
            sv.Value = chunks:sub((i - 1) * 200000 + 1, i * 200000)
        end

        local obj = Instance.new("ObjectValue", data)

        obj.Name = "Module"
        obj.Value = mod

        data.Parent = bridge

        repeat until SToI(buffer:sub(1, 4)) == id

        data:Destroy()

        if buffer:sub(5, 5) == "\0" then
            -- with the way we are replacing bytecode something could go catastrophically wrong if its gced
            table.insert(refs, mod)

            local fn = require(mod)
            local env = getfenv(fn)

            env.loadstring = loadstring

            return fn
        else
            local len = SToI(buffer:sub(6, 10))

            return nil, buffer:sub(11, 11 + len)
        end
    end

    spawn(function()
        for i = 10, 1, -1 do
            print(i)
            wait(1)
        end

        print(loadstring)

        local s, e = loadstring("print('hello world') print(loadstring)")

        print(s,e)

        if s then
            s()
        end
    end)
end

return {
    SetVisibility = function() end,
    HideTemp = function() end,

    -- prevents gc
    __buffer = buffer
}