import requests
import statistics
from datetime import datetime

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

# aktualne ustawienia (TU WPISUJESZ SWOJE)
AKTUALNA_KRZYWA = 0.3
AKTUALNY_DOLNY_PUNKT = 24  # °C

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
    now = datetime.utcnow()
    past = []
    future = []

    for t, temp in data:
        dt = datetime.fromisoformat(t)
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
# LOGIKA DECYZYJNA
# =========================

def recommend_curve(avg_temp_7d):
    """
    Bardzo uproszczony model:
    - im zimniej, tym wyższa krzywa
    """
    if avg_temp_7d > 5:
        return 0.2
    elif avg_temp_7d > 0:
        return 0.3
    elif avg_temp_7d > -5:
        return 0.4
    elif avg_temp_7d > -10:
        return 0.5
    elif avg_temp_7d > -15:
        return 0.6
    else:
        return 0.7

def clamp_curve(value):
    value = round(value / KRZYWA_KROK) * KRZYWA_KROK
    return min(max(value, KRZYWA_MIN), KRZYWA_MAX)

def recommend_lower_point(avg_temp_7d):
    if avg_temp_7d > 5:
        return 22
    elif avg_temp_7d > 0:
        return 24
    elif avg_temp_7d > -5:
        return 26
    elif avg_temp_7d > -10:
        return 28
    else:
        return 30

# =========================
# MAIN
# =========================

def main():
    data = get_weather()
    past, future = split_data(data)

    avg_7d = avg_last_days(past, 7)
    avg_14d_forecast = avg_next_days(future, 7)

    rec_curve = clamp_curve(recommend_curve(avg_7d))
    rec_lower = recommend_lower_point(avg_7d)

    print("\n=== ANALIZA OGRZEWANIA ===")
    print(f"Średnia temp. ostatnie 7 dni: {avg_7d:.1f} °C")
    print(f"Średnia prognoza 7 dni: {avg_14d_forecast:.1f} °C\n")

    print(f"Aktualna krzywa: {AKTUALNA_KRZYWA}")
    print(f"Rekomendowana krzywa: {rec_curve}")

    print(f"Aktualny dolny punkt: {AKTUALNY_DOLNY_PUNKT} °C")
    print(f"Rekomendowany dolny punkt: {rec_lower} °C\n")

    if rec_curve != AKTUALNA_KRZYWA:
        print(" ZMIANA KRZYWEJ ZALECANA (trend wielodniowy)")
    else:
        print(" Krzywa OK – nie zmieniaj")

    if rec_lower != AKTUALNY_DOLNY_PUNKT:
        print(" Skoryguj DOLNY PUNKT")
    else:
        print(" Dolny punkt OK")

    print("\nZasada:")
    print("- jeśli pojedyncze dni zimne → zmień tylko dolny punkt")
    print("- jeśli 5–7 dni trendu → zmień krzywą")

if __name__ == "__main__":
    main()
