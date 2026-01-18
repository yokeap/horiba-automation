#ifndef MESA_H
#define MESA_H
#include <Arduino.h>

#define HOME_ACT_CHAMBER A0

class Mesa
{
    public:
        Mesa() {}
        unsigned char pushSample(unsigned char state);
        unsigned char Measure(unsigned char state);
        unsigned char takeoffSample(unsigned char state);

    private:

};
#endif