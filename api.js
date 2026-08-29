/**
 * Vitalis AI — REST API Client
 */
const API_BASE = "";

async function request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const defaultHeaders = {
        "Content-Type": "application/json",
    };

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(url, config);
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `Request failed with status ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

const api = {
    // Health
    getHealth: () => request("/api/health"),

    // Profile
    getProfile: () => request("/api/profile"),
    updateProfile: (data) => request("/api/profile", {
        method: "PUT",
        body: JSON.stringify(data),
    }),

    // Meals
    getTodayMealPlan: () => request("/api/meals/today"),
    completeMeal: (mealId) => request(`/api/meals/${mealId}/complete`, { method: "POST" }),
    skipMeal: (mealId) => request(`/api/meals/${mealId}/skip`, { method: "POST" }),
    substituteMealItem: (mealId, originalFoodId, substituteFoodId, substituteQuantity, reason) => request(`/api/meals/${mealId}/substitute`, {
        method: "POST",
        body: JSON.stringify({
            original_food_id: originalFoodId,
            substitute_food_id: substituteFoodId,
            substitute_quantity: substituteQuantity,
            reason: reason || "User substitution",
        }),
    }),

    // Hydration
    getTodayHydration: () => request("/api/hydration/today"),
    logWater: (amountMl, source = "quick_button") => request("/api/hydration/log", {
        method: "POST",
        body: JSON.stringify({ amount_ml: amountMl, source }),
    }),
    deleteWaterLog: (logId) => request(`/api/hydration/${logId}`, { method: "DELETE" }),

    // Progress & Analytics
    getTodayProgress: () => request("/api/progress/today"),
    getWeeklyProgress: () => request("/api/progress/weekly"),

    // Foods Database
    searchFoods: (query = "", category = "") => {
        const params = new URLSearchParams();
        if (query) params.append("query", query);
        if (category) params.append("category", category);
        return request(`/api/foods?${params.toString()}`);
    },
    getFoodById: (foodId) => request(`/api/foods/${foodId}`),
    calculatePortion: (foodId, quantity, unit = "g") => request("/api/foods/calculate", {
        method: "POST",
        body: JSON.stringify({ food_id: foodId, quantity, unit }),
    }),
};

window.api = api;
