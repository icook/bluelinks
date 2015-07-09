vote = """
local direction = tonumber(ARGV[4])
local userid = tonumber(ARGV[3])
local post_key = ARGV[1] .. ARGV[2]
local status = tonumber(redis.call('HGET', post_key, userid))
if status == direction then
    return
end
local amount
if direction == 2 then
    if status == 0 then
        amount = 1
    else
        amount = -1
    end
    redis.call('HDEL', post_key, userid)
else
    redis.call('HSET', post_key, userid, direction)
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
end
redis.call('ZINCRBY', ARGV[5], amount, ARGV[2])
return
"""
