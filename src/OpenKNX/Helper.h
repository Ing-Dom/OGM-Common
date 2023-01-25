#pragma once
#include "knx.h"
#include <cstdint>
#include <stdio.h>
#include <stdarg.h>
#include <Arduino.h>

namespace OpenKNX
{
    class Helper
    {
      public:
        static void log(const char* prefix, const char* output, ...);
        static void logHex(const char* prefix, const uint8_t* data, size_t size);
    };
} // namespace OpenKNX