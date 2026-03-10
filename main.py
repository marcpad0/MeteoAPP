import requests
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import engine, get_db, Base
from user_class import User, FavoriteCity
from schemas import UserCreate, UserLogin, UserResponse, FavoriteCityResponse

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")


@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(name=user.name, email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or user.password != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"message": "Login successful", "user_id": user.id, "name": user.name, "email": user.email}


def geocode_city(city: str):
    geo_response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1}
    )
    if geo_response.status_code != 200:
        return None, None
    results = geo_response.json().get("results")
    if not results:
        return None, None
    return results[0]["latitude"], results[0]["longitude"]


@app.get("/weather")
def get_weather(city: str):
    lat, lon = geocode_city(city)
    if lat is None:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        current_weather = data.get("current_weather", {})
        temperature = current_weather.get("temperature")
        weather_code = current_weather.get("weathercode")
        return {"city": city, "temperature": temperature, "weather_code": weather_code}
    else:
        return {"error": "Unable to fetch weather data"}

@app.get("/next_days_weather")
def get_next_days_weather(city: str):
    lat, lon = geocode_city(city)
    if lat is None:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=auto"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        daily_weather = data.get("daily", {})
        return {"city": city, "daily_weather": daily_weather}
    else:
        return {"error": "Unable to fetch daily weather data"}

@app.post("/users/{user_id}/favorite-cities", response_model=FavoriteCityResponse)
def save_favorite_city(user_id: int, city: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    lat, lon = geocode_city(city)
    if lat is None:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    existing = db.query(FavoriteCity).filter(FavoriteCity.user_id == user_id, FavoriteCity.city == city).first()
    if existing:
        raise HTTPException(status_code=400, detail="City already in favorites")
    favorite = FavoriteCity(user_id=user_id, city=city)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


@app.get("/users/{user_id}/favorite-cities", response_model=list[FavoriteCityResponse])
def get_favorite_cities(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.favorite_cities


@app.delete("/users/{user_id}/favorite-cities/{city}")
def delete_favorite_city(user_id: int, city: str, db: Session = Depends(get_db)):
    favorite = db.query(FavoriteCity).filter(FavoriteCity.user_id == user_id, FavoriteCity.city == city).first()
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite city not found")
    db.delete(favorite)
    db.commit()
    return {"message": f"'{city}' removed from favorites"}


@app.get("/users/{user_id}/favorite-cities/weather")
def get_favorites_weather(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    results = []
    for fav in user.favorite_cities:
        lat, lon = geocode_city(fav.city)
        if lat is None:
            results.append({"city": fav.city, "error": "Could not fetch coordinates"})
            continue
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url)
        if response.status_code == 200:
            cw = response.json().get("current_weather", {})
            results.append({"city": fav.city, "temperature": cw.get("temperature"), "weather_code": cw.get("weathercode")})
        else:
            results.append({"city": fav.city, "error": "Unable to fetch weather"})
    return results


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)