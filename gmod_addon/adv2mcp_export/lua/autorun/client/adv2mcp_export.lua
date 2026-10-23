-- Exports model paths only; never spawns props or changes server settings.
local outputPath = "advdupe2/adv2mcp/server-props.json"

local function allowedName(name)
    name = tostring(name or "")
    return string.find(name, "Разреш", 1, true) or string.find(name, "разреш", 1, true)
        or string.find(string.lower(name), "allowed prop", 1, true)
end

local function normalize(model)
    if not isstring(model) then return nil end
    model = string.lower(string.Replace(model, "\\", "/"))
    if string.sub(model, 1, 7) ~= "models/" or string.sub(model, -4) ~= ".mdl" then return nil end
    return model
end

local function addModel(found, model, category)
    model = normalize(model)
    if not model then return end
    local entry = { model = model, category = category }
    if util.IsValidModel then entry.available = util.IsValidModel(model) end
    if util.GetModelBounds then
        local ok, mins, maxs = pcall(util.GetModelBounds, model)
        if ok and isvector(mins) and isvector(maxs) then
            entry.hull_min = {mins.x, mins.y, mins.z}
            entry.hull_max = {maxs.x, maxs.y, maxs.z}
        end
    end
    found[model] = entry
end

local function save(found, source, merge)
    local count = table.Count(found)
    if count == 0 then
        print("[adv2mcp] No prop paths found; the existing profile was not changed.")
        return
    end
    local server = game.GetIPAddress()
    local old = util.JSONToTable(file.Read(outputPath, "DATA") or "")
    if merge and istable(old) and old.server == server and istable(old.models) then
        for _, entry in ipairs(old.models) do
            if istable(entry) and isstring(entry.model) and not found[entry.model] then
                found[entry.model] = entry
            end
        end
    end
    local models = {}
    for _, model in ipairs(table.GetKeys(found)) do models[#models+1] = found[model] end
    table.sort(models, function(a,b) return a.model < b.model end)
    local profile = {format="adv2mcp-props-v1", server=server, source=source,
        exported_at=os.date("!%Y-%m-%dT%H:%M:%SZ"), models=models}
    local json = util.TableToJSON(profile, true)
    if not json then print("[adv2mcp] Could not serialize profile.") return end
    file.CreateDir("advdupe2/adv2mcp")
    if file.Exists(outputPath, "DATA") then
        file.Write("advdupe2/adv2mcp/server-props-backup.json", file.Read(outputPath, "DATA"))
    end
    file.Write(outputPath, json)
    print("[adv2mcp] Captured "..count.." paths; profile now has "..#models.." models: data/"..outputPath)
    print("[adv2mcp] MCP will reload the profile on its next tool call.")
end

concommand.Add("adv2mcp_export_props", function()
    local found = {}
    local function readCategories(categories)
        for _, category in pairs(categories or {}) do
            if istable(category) and allowedName(category.name) then
                for _, item in pairs(category.contents or {}) do
                    if istable(item) and item.type == "model" then addModel(found, item.model, category.name) end
                end
            end
        end
    end
    if spawnmenu.GetPropTable then readCategories(spawnmenu.GetPropTable()) end
    if spawnmenu.GetCustomPropTable then readCategories(spawnmenu.GetCustomPropTable()) end
    if table.Count(found) == 0 then
        print("[adv2mcp] Open the Q menu once, then retry. For custom tabs use adv2mcp_capture_props.")
        return
    end
    save(found, "allowed spawnmenu categories", false)
end)

-- Custom server menus often bypass spawnmenu's category tables. Capture the
-- active 'Allowed props' property-sheet tab after a delay, so the user can
-- close the console and hold Q. Walk the full tab, including clipped icons.
concommand.Add("adv2mcp_capture_props", function(_, _, args)
    local delay = math.Clamp(tonumber(args[1]) or 5, 2, 30)
    print("[adv2mcp] In "..delay.." seconds: close console, hold Q and select an Allowed props tab.")
    timer.Simple(delay, function()
        local found, visited = {}, {}
        local function collect(panel, category)
            if not IsValid(panel) then return end
            local model
            if panel.GetModelName then model = panel:GetModelName() end
            if not model and panel.GetSpawnName then model = panel:GetSpawnName() end
            if not model and panel.GetModel then
                local value = panel:GetModel()
                if isstring(value) then model = value end
            end
            if model then addModel(found, model, category) end
            for _, child in ipairs(panel:GetChildren()) do collect(child, category) end
        end
        local function walk(panel)
            if not IsValid(panel) or not panel:IsVisible() or visited[panel] then return end
            visited[panel] = true
            if panel.GetActiveTab and istable(panel.Items) then
                local active = panel:GetActiveTab()
                if IsValid(active) and active.GetText and allowedName(active:GetText()) then
                    for _, item in pairs(panel.Items) do
                        if item.Tab == active and IsValid(item.Panel) then collect(item.Panel, active:GetText()) end
                    end
                end
            end
            for _, child in ipairs(panel:GetChildren()) do walk(child) end
        end
        walk(vgui.GetWorldPanel())
        save(found, "selected allowed-prop menu tabs", true)
    end)
end)

print("[adv2mcp] Prop exporter ready: adv2mcp_export_props / adv2mcp_capture_props")
