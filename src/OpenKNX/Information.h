#include "knxprod.h"
#include <knx.h>

namespace OpenKNX
{

    struct Information
    {
        uint16_t _applicationNumber = 0;
        uint8_t _applicationVersion = 0;
        uint8_t _firmwareRevision = 0;

        uint16_t applicationNumber()
        {
            return _applicationNumber;
        }

        void applicationNumber(uint16_t applicationNumber)
        {
            _applicationNumber = applicationNumber;
        }

        char* humanApplicationNumber()
        {
            char* buffer = new char[6];
            sprintf(buffer, "0x%04X", applicationNumber());
            return buffer;
        }

        uint16_t applicationVersion()
        {
            return _applicationVersion;
        }

        void applicationVersion(uint8_t applicationVersion)
        {
            _applicationVersion = applicationVersion;
        }

        char* humanApplicationVersion()
        {
            char* buffer = new char[5];
            sprintf(buffer, "%i.%i", ((applicationVersion() & 0xF0) >> 4), (applicationVersion() & 0x0F));
            return buffer;
        }

        uint16_t firmwareNumber()
        {
            return (MAIN_OpenKnxId << 8) + MAIN_ApplicationNumber;
        }

        char* humanFirmwareNumber()
        {
            char* buffer = new char[6];
            sprintf(buffer, "0x%04X", firmwareNumber());
            return buffer;
        }

        uint16_t firmwareVersion()
        {
            return ((_firmwareRevision & 0x1F) << 11) | ((MAIN_ApplicationVersion & 0xF0) << 2) | (MAIN_ApplicationVersion & 0x0F);
        }

        void firmwareRevision(uint8_t firmwareRevision)
        {
            _firmwareRevision = firmwareRevision;
        }

        char* humanFirmwareVersion()
        {
            char* buffer = new char[20];
            sprintf(buffer, "%i.%i.%i", ((firmwareVersion() & 0x03C0)), (firmwareVersion() & 0x000F), ((firmwareVersion() & 0xF800) >> 11));
            return buffer;
        }

        uint16_t individualAddress()
        {
            return knx.individualAddress();
        }

        char* humanIndividualAddress()
        {
            char* buffer = new char[10];
            sprintf(buffer, "%i.%i.%i", ((knx.individualAddress() & 0xF000) >> 12), ((knx.individualAddress() & 0x0F00) >> 8), (knx.individualAddress() & 0x00FF));
            return buffer;
        }
    };

} // namespace OpenKNX