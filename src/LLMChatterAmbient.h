#ifndef MOD_LLM_CHATTER_AMBIENT_H
#define MOD_LLM_CHATTER_AMBIENT_H

#include "Define.h"
#include "SharedDefines.h"

#include <string>
#include <vector>

class Weather;
enum WeatherState : uint32;

std::vector<uint32> GetZonesWithRealPlayers();
void HandleAmbientGameEventStart(uint16 eventId);
void HandleAmbientGameEventStop(uint16 eventId);
void HandleWeatherChange(
    Weather* weather, WeatherState state,
    float grade);
void CheckDayNightTransition(
    std::string& lastTimePeriod);
void CheckAmbientWeather();
void CheckActiveHolidays();
void TryTriggerChatter();

#endif
