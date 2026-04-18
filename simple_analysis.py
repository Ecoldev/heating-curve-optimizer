import requests
import statistics
from datetime import datetime, timezone

# =========================
# KONFIGURACJA
# =========================

LAT = 49.9752
LON = 19.8287

API_URL = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&hourly=temperature_2m"
    "&past_days=31"
    "&forecast_days=16"
)

TEMP_PROJEKTOWA = -20
MAX_ZASILANIA = 45

KRZYWA_MIN = 0.1
KRZYWA_MAX = 4.0
KRZYWA_KROK = 0.1

# Twoje aktualne ustawienia
AKTUALNA_KRZYWA = 0.3
AKTUALNY_DOLNY_PUNKT = 24  # °C

# histereza
HISTEREZA_KRZYWA = 0.1
HISTEREZA_TEMP = 1

# =========================
# POBRANIE DANYCH
# =========================

def get_weather():
    r = requests.get(API_URL, timeout=10)
    r.raise_for_status()
    data = r.json()

    temps = data["hourly"]["temperature_2m"]
    times = data["hourly"]["time"]

    return list(zip(times, temps))

# =========================
# ANALIZA
# =========================

def split_data(data):
    now = datetime.now(timezone.utc)

    past = []
    future = []

    for t, temp in data:
        dt = datetime.fromisoformat(t).replace(tzinfo=timezone.utc)

        if dt < now:
            past.append(temp)
        else:
            future.append(temp)

    return past, future

def avg_last_days(data, days):
    hours = days * 24
    return statistics.mean(data[-hours:])

def avg_next_days(data, days):
    hours = days * 24
    return statistics.mean(data[:hours])

# =========================
# LOGIKA – KRZYWA
# =========================

def recommend_curve(avg_temp):
    """
    Model liniowy:
    10°C -> 0.2
    -20°C -> 0.7
    """
    curve = 0.2 + (10 - avg_temp) * (0.5 / 30)
    return curve

def adjust_for_trend(curve, trend):
    """
    Korekta predykcyjna
    """
    if trend < -2:
        curve += 0.1
    elif trend > 2:
        curve -= 0.1
    return curve

def clamp_curve(value):
    value = round(value / KRZYWA_KROK) * KRZYWA_KROK
    return min(max(value, KRZYWA_MIN), KRZYWA_MAX)

def should_change_curve(current, recommended):
    return abs(current - recommended) >= HISTEREZA_KRZYWA

# =========================
# LOGIKA – DOLNY PUNKT
# =========================

def recommend_lower_point(avg_temp, trend):
    """
    Dynamiczny dolny punkt
    """
    base = 22 + (5 - avg_temp) * 0.5

    if trend < -2:
        base += 1
    elif trend > 2:
        base -= 1

    return round(base)

def should_change_temp(current, recommended):
    return abs(current - recommended) >= HISTEREZA_TEMP

# =========================
# MAIN
# =========================

def main():
    data = get_weather()
    past, future = split_data(data)

    avg_7d = avg_last_days(past, 7)
    avg_7d_forecast = avg_next_days(future, 7)

    trend = avg_7d_forecast - avg_7d

    # KRZYWA
    rec_curve = recommend_curve(avg_7d)
    rec_curve = adjust_for_trend(rec_curve, trend)
    rec_curve = clamp_curve(rec_curve)

    # DOLNY PUNKT
    rec_lower = recommend_lower_point(avg_7d, trend)

    # =========================
    # OUTPUT
    # =========================

    print("\n=== ANALIZA OGRZEWANIA ===")
    print(f"Średnia temp. ostatnie 7 dni: {avg_7d:.1f} °C")
    print(f"Średnia prognoza 7 dni: {avg_7d_forecast:.1f} °C")
    print(f"Trend: {trend:+.1f} °C\n")

    print(f"Aktualna krzywa: {AKTUALNA_KRZYWA}")
    print(f"Rekomendowana krzywa: {rec_curve}")

    if should_change_curve(AKTUALNA_KRZYWA, rec_curve):
        print(" ZMIANA KRZYWEJ ZALECANA")
    else:
        print(" Krzywa OK – bez zmian")

    print()

    print(f"Aktualny dolny punkt: {AKTUALNY_DOLNY_PUNKT} °C")
    print(f"Rekomendowany dolny punkt: {rec_lower} °C")

    if should_change_temp(AKTUALNY_DOLNY_PUNKT, rec_lower):
        print(" Skoryguj DOLNY PUNKT")
    else:
        print(" Dolny punkt OK")

    print("\nZasada sterowania:")
    print("- krótkie skoki temperatur → dolny punkt")
    print("- trend 5–7 dni → krzywa")
    print("- prognoza zmienia trend → reaguj wcześniej")

# =========================

if __name__ == "__main__":
    main()