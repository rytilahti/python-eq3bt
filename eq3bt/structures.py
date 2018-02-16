""" Contains construct adapters and structures. """
from construct import Struct, Adapter, ExprAdapter, Int8ub, Enum, FlagsEnum, Const, Pass, GreedyRange, GreedyBytes, IfThenElse, If, Bytes, Byte
import struct
from datetime import datetime, time
from math import floor

PROP_INFO_RETURN = 2
PROP_SCHEDULE_SET = 0x10
PROP_SCHEDULE_RETURN = 0x21

NAME_TO_DAY = {"sat": 0, "sun": 1, "mon": 2, "tue": 3, "wed": 4, "thu": 5, "fri": 6}
NAME_TO_CMD = {"write": PROP_SCHEDULE_SET, "response": PROP_SCHEDULE_RETURN}
HOUR_24_PLACEHOLDER = 1234


class TimeAdapter(Adapter):
    """ Adapter to encode and decode schedule times. """
    def _decode(self, obj, ctx, path):
        h, m = divmod(obj * 10, 60)
        if h == 24:  # HACK, can we do better?
            return HOUR_24_PLACEHOLDER
        return time(hour=h, minute=m)

    def _encode(self, obj, ctx, path):
        # TODO: encode h == 24 hack
        if obj == HOUR_24_PLACEHOLDER:
            return int(24 * 60 / 10)
        encoded = int((obj.hour * 60 + obj.minute) / 10)
        return encoded

class TempAdapter(Adapter):
    """ Adapter to encode and decode temperature. """
    def _decode(self, obj, ctx, path):
        return float(obj / 2.0)

    def _encode(self, obj, ctx, path):
        return int(obj * 2.0)

ModeFlags = "ModeFlags" / FlagsEnum(Int8ub,
                                    AUTO=0x00, # always True, doesnt affect building
                                    MANUAL=0x01,
                                    AWAY=0x02,
                                    BOOST=0x04,
                                    DST=0x08,
                                    WINDOW=0x10,
                                    LOCKED=0x20,
                                    UNKNOWN=0x40,
                                    LOW_BATTERY=0x80)


class AwayDataAdapter(Adapter):
    """ Adapter to encode and decode away data. """
    def _decode(self, obj, ctx, path):
        (day, year, hour_min, month) = obj
        year += 2000

        min = 0
        if hour_min & 0x01:
            min = 30
        hour = int(hour_min / 2)

        return datetime(year=year, month=month, day=day, hour=hour, minute=min)

    def _encode(self, obj, ctx, path):
        if obj.year < 2000 or obj.year > 2099:
            raise Exception("Invalid year, possible [2000,2099]")
        year = obj.year - 2000
        hour = obj.hour * 2
        if obj.minute:  # we encode all minute values to h:30
            hour |= 0x01
        return (obj.day, year, hour, obj.month)


Status = "Status" / Struct(
    "cmd" / Const(PROP_INFO_RETURN, Int8ub),
    Const(0x01, Int8ub),
    "mode" / ModeFlags,
    "valve" / Int8ub,
    Const(0x04, Int8ub),
    "target_temp" / TempAdapter(Int8ub),
    "away" / IfThenElse(lambda ctx: ctx.mode.AWAY, 
        AwayDataAdapter(Byte[4]),
        GreedyBytes),
)

Schedule = "Schedule" / Struct(
    "cmd" / Enum(Int8ub, **NAME_TO_CMD),
    "day" / Enum(Int8ub, **NAME_TO_DAY),
    "base_temp" / TempAdapter(Int8ub),
    "next_change_at" / TimeAdapter(Int8ub),
    "hours" / GreedyRange(Struct(
        "target_temp" / TempAdapter(Int8ub),
        "next_change_at" / TimeAdapter(Int8ub),
    )),
)
