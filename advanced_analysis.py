# =========================
# IMPORTY
# =========================
import matplotlib
matplotlib.use("TkAgg")

import requests
import statistics
from datetime import datetime
import matplotlib.pyplot as plt

# =========================
# KONFIGURACJA
# =========================

LAT = 49.9752
LON = 19.8558

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&hourly=temperature_2m,apparent_temperature,wind_speed_10m,"
    "cloud_cover"
    "&past_days=92"
    "&forecast_days=16"
    "&timezone=Europe%2FBerlin"
)

IMGW_URL = "https://danepubliczne.imgw.pl/api/data/synop/id/12566"

AKTUALNA_KRZYWA = 0.3
AKTUALNY_DOLNY_PUNKT = 24
MAX_ZASILANIA = 45

KRZYWA_MIN = 0.1
KRZYWA_MAX = 0.4
KRZYWA_KROK = 0.1

# =========================
# POGODA
# =========================
def get_current_temp_imgw():
    r = requests.get(IMGW_URL, timeout=10)
    r.raise_for_status()
    return float(r.json()["temperatura"])

def get_weather_open_meteo():
    r = requests.get(OPEN_METEO_URL, timeout=10)
    r.raise_for_status()
    d = r.json()["hourly"]
    return (
        d["time"],
        d["temperature_2m"],
        d["apparent_temperature"],
        d["wind_speed_10m"],
        d["cloud_cover"],
    )

# =========================
# MODEL PODŁOGÓWKI
# =========================
def zasilanie(temp_zew, krzywa, dolny):
    return min(dolny + krzywa * (20 - temp_zew), MAX_ZASILANIA)

# =========================
# REKOMENDACJA (ULEPSZONA)
# =========================
def recommend(avg_temp, avg_apparent, avg_wind, avg_cloud):

    curve = 0.4
    lower = 22

    # baza: temperatura
    if avg_temp > 5:
        curve -= 0.1
        lower -= 1
    elif avg_temp < -10:
        curve += 0.1
        lower += 1

    # odczuwalna (wiatr + wilgoć)
    if avg_apparent < avg_temp - 2:
        curve += 0.1

    # wiatr
    if avg_wind > 5:
        lower += 1

    # zachmurzenie (brak zysków)
    if avg_cloud > 70:
        lower += 1

    curve = round(curve / KRZYWA_KROK) * KRZYWA_KROK
    curve = min(max(curve, KRZYWA_MIN), KRZYWA_MAX)

    return curve, lower

def what_to_adjust(curve_now, lower_now, curve_rec, lower_rec):
    if abs(curve_rec - curve_now) > abs(lower_rec - lower_now) / 5:
        return "👉 Lepiej ruszyć KRZYWĄ"
    elif lower_rec != lower_now:
        return "👉 Lepiej ruszyć DOLNYM PUNKTEM"
    else:
        return "👉 Ustawienia OK"

# =========================
# WYKRES KRZYWEJ
# =========================
def draw_curve(curve_now, lower_now, curve_rec, lower_rec, temp_now):
    temps = list(range(20, -26, -1))

    y_now = [zasilanie(t, curve_now, lower_now) for t in temps]
    y_rec = [zasilanie(t, curve_rec, lower_rec) for t in temps]

    z_now = zasilanie(temp_now, curve_now, lower_now)

    plt.figure(figsize=(10, 6))
    plt.plot(temps, y_now, label="Aktualna krzywa", linewidth=2)
    plt.plot(temps, y_rec, "--", label="Rekomendowana", linewidth=2)

    plt.axvline(temp_now, color="red", linestyle="--")
    plt.axhline(z_now, color="red", linestyle=":")
    plt.scatter(temp_now, z_now, color="red")

    plt.xlabel("Temperatura zewnętrzna [°C]")
    plt.ylabel("Temperatura zasilania [°C]")
    plt.title("Krzywa grzewcza – punkt pracy")
    plt.grid(True)
    plt.legend()
    plt.show()

# =========================
# WYKRES CZASOWY
# =========================
def draw_time_curve(times, temps, curve, lower):
    zasilania = [zasilanie(t, curve, lower) for t in temps]
    times_s = [datetime.fromisoformat(t).strftime("%d-%m %H:%M") for t in times]

    plt.figure(figsize=(12, 6))
    plt.plot(times_s, temps, label="Temp. zewnętrzna")
    plt.plot(times_s, zasilania, label="Zasilanie z krzywej")
    plt.xticks(times_s[::6], rotation=45)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

# =========================
# MAIN
# =========================
def main():
    temp_now = get_current_temp_imgw()
    times, temps, app, wind, cloud = get_weather_open_meteo()

    avg_temp = statistics.mean(temps[-168:])
    avg_app = statistics.mean(app[-168:])
    avg_wind = statistics.mean(wind[-168:])
    avg_cloud = statistics.mean(cloud[-168:])

    curve_rec, lower_rec = recommend(avg_temp, avg_app, avg_wind, avg_cloud)

    print("\n=== ANALIZA OGRZEWANIA ===\n")
    print(f"Aktualna temp. IMGW: {temp_now:.1f} °C")
    print(f"Śr. 7 dni: {avg_temp:.1f} °C")
    print(f"Śr. odczuwalna: {avg_app:.1f} °C")
    print(f"Wiatr: {avg_wind:.1f} m/s")
    print(f"Zachmurzenie: {avg_cloud:.0f} %\n")

    print(f"Aktualna krzywa: {AKTUALNA_KRZYWA}")
    print(f"Rekomendowana: {curve_rec}")

    print(f"Aktualny dolny: {AKTUALNY_DOLNY_PUNKT} °C")
    print(f"Rekomendowany: {lower_rec} °C\n")

    print(what_to_adjust(
        AKTUALNA_KRZYWA,
        AKTUALNY_DOLNY_PUNKT,
        curve_rec,
        lower_rec
    ))

    draw_curve(
        AKTUALNA_KRZYWA,
        AKTUALNY_DOLNY_PUNKT,
        curve_rec,
        lower_rec,
        temp_now
    )

    draw_time_curve(times[-48:], temps[-48:], AKTUALNA_KRZYWA, AKTUALNY_DOLNY_PUNKT)

    input("\nEnter aby zakończyć...")

if __name__ == "__main__":
    main()
