vote = """
local direction = tonumber(ARGV[4])
local userid = tonumber(ARGV[3])
local post_key = ARGV[1] .. ARGV[2]
local status = tonumber(redis.call('HGET', post_key, userid))
if status == direction then
    return
end
redis.call('HSET', post_key, userid, direction)
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
redis.call('ZINCRBY', ARGV[5], amount, ARGV[2])
return
"""
