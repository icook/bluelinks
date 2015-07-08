from datetime import datetime, timedelta
from math import log

epoch = datetime(1970, 1, 1)

def hot(int score, date):
    order = log(max(abs(score), 1), 10)
    cdef int sign = 1 if score > 0 else -1 if score < 0 else 0
    td = date - epoch
    cdef float seconds = td.days * 86400 + td.seconds + (float(td.microseconds) / 1000000)
    seconds -= 1436202440
    return round(sign * order + seconds / 45000, 7)
