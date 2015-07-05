vote = """
local direction = tonumber(ARGV[3])
local userid = tonumber(ARGV[2])
local status = tonumber(redis.call('HGET', ARGV[1], userid))
if status == direction then
    return
end
redis.call('HSET', ARGV[1], userid, direction)
local amount
if direction == 0 then
    amount = -1
else
    amount = 1
end
if status == 1 then
    amount = amount - 1
end
if status == 0 then
    amount = amount + 1
end
redis.call('HINCRBY', ARGV[1], 'score', amount)
return
"""
