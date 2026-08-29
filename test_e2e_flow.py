import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.seed import seed_all

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def init_test_app():
    seed_all()

def test_full_system_flow():
    print("--- 1. Testing Frontend Static Serving & Health ---")
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "Vitalis AI" in res_index.text
    print("[OK] Root index.html served properly")

    res_css = client.get("/static/css/styles.css")
    assert res_css.status_code == 200
    print("[OK] CSS stylesheet served properly")

    res_js = client.get("/static/js/app.js")
    assert res_js.status_code == 200
    print("[OK] JS application logic served properly")

    res_health = client.get("/api/health").json()
    assert res_health["status"] == "healthy"
    print("[OK] Health check API healthy:", res_health)

    print("\n--- 2. Testing Profile & Personalized Target Calculations ---")
    prof = client.get("/api/profile").json()
    assert prof["name"] == "Alex Morgan"
    assert prof["target_protein_g"] > 0
    print(f"[OK] Profile verified: {prof['name']} | Calories: {prof['target_calories']} kcal | Protein: {prof['target_protein_g']}g | Water: {prof['target_water_ml']}ml")

    print("\n--- 3. Testing Daily Meal Schedule & Portion Calculation ---")
    plan = client.get("/api/meals/today").json()
    assert len(plan["meals"]) == 5
    first_meal = plan["meals"][0]
    print(f"[OK] Loaded {len(plan['meals'])} meals. First meal: {first_meal['name']} ({first_meal['meal_type']}) - {first_meal['calories']} kcal, {first_meal['protein']}g protein, {first_meal['fiber']}g fiber")
    assert first_meal["calories"] < 800  # realistic calorie range

    print("\n--- 4. Testing Meal Completion & Live Telemetry Sync ---")
    comp_res = client.post(f"/api/meals/{first_meal['id']}/complete").json()
    assert comp_res["status"] == "success"
    
    prog = client.get("/api/progress/today").json()
    assert prog["summary"]["meals_completed"] == 1
    assert prog["summary"]["adherence_score"] == 20.0
    print(f"[OK] Meal marked completed! Adherence: {prog['summary']['adherence_score']}% | Consumed Protein: {prog['summary']['protein']['consumed_g']}g")

    print("\n--- 5. Testing Hydration Real-Time Tracking ---")
    water_res = client.post("/api/hydration/log", json={"amount_ml": 250.0, "source": "quick_button"}).json()
    assert water_res["status"] == "success"
    
    hydra = client.get("/api/hydration/today").json()
    assert hydra["consumed_ml"] >= 250.0
    print(f"[OK] Hydration logged: {hydra['consumed_ml']} / {hydra['target_ml']} ml ({hydra['percentage']}%)")

    print("\n--- 6. Testing Food Database Search & Deterministic Calculation ---")
    foods = client.get("/api/foods?query=Tofu").json()
    assert len(foods) > 0
    tofu = foods[0]
    calc = client.post("/api/foods/calculate", json={"food_id": tofu["food_id"], "quantity": 100.0, "unit": "g"}).json()
    assert calc["nutrition"]["protein"] == tofu["protein_per_100g"]
    print(f"[OK] Food calculation verified: 100g {tofu['name']} = {calc['nutrition']['protein']}g protein, {calc['nutrition']['calories']} kcal")

    print("\n--- 7. Testing Intelligent Ingredient Substitution ---")
    lunch = plan["meals"][2]
    sub_res = client.post(
        f"/api/meals/{lunch['id']}/substitute",
        json={
            "original_food_id": "food_012",
            "substitute_food_id": "food_011",
            "substitute_quantity": 80.0,
            "reason": "Plant-based preference"
        }
    ).json()
    assert sub_res["status"] == "success"
    print(f"[OK] Substitution verified: {sub_res['message']}")

    print("\n--- 8. Testing Weekly Analytics ---")
    weekly = client.get("/api/progress/weekly").json()
    assert len(weekly["days"]) == 7
    print(f"[OK] Weekly analytics loaded: {len(weekly['days'])} days tracked, avg adherence: {weekly['weekly_averages']['adherence']}%")

    print("\n[ALL TESTS PASSED] End-to-end integration verified successfully.")
