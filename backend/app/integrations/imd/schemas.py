from typing import Optional, List, Any
from pydantic import BaseModel, Field

class IMDCityForecastItem(BaseModel):
    Date: Optional[str] = None
    Station_Code: Optional[str] = None
    Station_Name: Optional[str] = None
    Today_Max_temp: Optional[Any] = None
    Today_Min_temp: Optional[Any] = None
    Past_24_hrs_Rainfall: Optional[Any] = None
    Relative_Humidity_at_0830: Optional[Any] = None
    Relative_Humidity_at_1730: Optional[Any] = None
    Todays_Forecast: Optional[str] = None

class IMDDistrictNowcastItem(BaseModel):
    State_Name: Optional[str] = None
    District_Name: Optional[str] = None
    Nowcast_Issued_At: Optional[str] = None
    Valid_Upto: Optional[str] = None
    Warning_Color: Optional[str] = None # Green, Yellow, Orange, Red
    Warning_Message: Optional[str] = None

class IMDDistrictRainfallItem(BaseModel):
    State_Name: Optional[str] = None
    District_Name: Optional[str] = None
    Actual_Rainfall_mm: Optional[float] = 0.0
    Normal_Rainfall_mm: Optional[float] = 0.0
    Departure_pct: Optional[float] = 0.0
    Date: Optional[str] = None

class IMDDistrictWarningItem(BaseModel):
    State_Name: Optional[str] = None
    District_Name: Optional[str] = None
    Day_1_Warning: Optional[str] = None
    Day_1_Color: Optional[str] = None
    Day_2_Warning: Optional[str] = None
    Day_2_Color: Optional[str] = None
    Issued_On: Optional[str] = None

class IMDAwsArgItem(BaseModel):
    Station_Code: Optional[str] = None
    Station_Name: Optional[str] = None
    State: Optional[str] = None
    District: Optional[str] = None
    DateTime_IST: Optional[str] = None
    Temperature_C: Optional[float] = None
    Relative_Humidity_Pct: Optional[float] = None
    Rainfall_Hourly_mm: Optional[float] = None
    Rainfall_Cumulative_24h_mm: Optional[float] = None
    Wind_Speed_Kmph: Optional[float] = None
    Wind_Direction_Deg: Optional[float] = None
