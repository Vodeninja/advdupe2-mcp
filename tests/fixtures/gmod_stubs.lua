-- Minimal stand-ins for upstream codec interoperability tests.
AdvDupe2 = {LegacyDecoders={}}
CLIENT = false
TYPE_TABLE, TYPE_BOOL, TYPE_NUMBER, TYPE_VECTOR, TYPE_ANGLE, TYPE_STRING = 1,2,3,4,5,6
function include() end
function AddCSLuaFile() end
function ErrorNoHalt(message) error(message) end
function Vector(x,y,z) return {__kind=TYPE_VECTOR,x=x or 0,y=y or 0,z=z or 0} end
function Angle(p,y,r) return {__kind=TYPE_ANGLE,p=p or 0,y=y or 0,r=r or 0} end
function TypeID(value)
    if type(value)=="table" then return value.__kind or TYPE_TABLE end
    return ({boolean=TYPE_BOOL,number=TYPE_NUMBER,string=TYPE_STRING})[type(value)] or 0
end
util = {Compress=py_compress, Decompress=py_decompress}
local files = {}
local methods = {}
function methods:Write(data)
    self.data = self.data:sub(1,self.pos)..data..self.data:sub(self.pos+#data+1)
    self.pos = self.pos+#data
end
function methods:WriteByte(value) self:Write(string.char(value)) end
function methods:WriteShort(value) self:Write(string.pack("<i2",value)) end
function methods:WriteULong(value) self:Write(string.pack("<I4",value)) end
function methods:WriteDouble(value) self:Write(string.pack("<d",value)) end
function methods:Read(size)
    if self.pos+size>#self.data then error("EOF") end
    local data = self.data:sub(self.pos+1,self.pos+size)
    self.pos = self.pos+size
    return data
end
function methods:ReadByte()
    if self.pos>=#self.data then return nil end
    return self:Read(1):byte()
end
function methods:ReadShort() return (string.unpack("<i2",self:Read(2))) end
function methods:ReadULong() return (string.unpack("<I4",self:Read(4))) end
function methods:ReadDouble() return (string.unpack("<d",self:Read(8))) end
function methods:Tell() return self.pos end
function methods:Seek(pos) self.pos=pos end
function methods:Size() return #self.data end
function methods:Flush() files[self.name]=self.data end
function methods:Close() self:Flush() end
file = {}
function file.Open(name,mode)
    return setmetatable({name=name,pos=0,data=mode=="wb" and "" or files[name] or ""}, {__index=methods})
end
