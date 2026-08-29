/**
 * Vitalis AI — Frontend Application Logic & Reactive Controller
 */

let state = {
    profile: null,
    mealPlan: null,
    hydration: null,
    progress: null,
    allFoods: [],
    charts: {
        macroChart: null,
        weeklyChart: null
    }
};

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

async function initApp() {
    setupNavigation();
    setupDateDisplay();
    
    // Initial Load
    try {
        await Promise.all([
            loadProfile(),
            loadMealPlan(),
            loadHydration(),
            loadProgress(),
            loadFoods()
        ]);
        showToast("Welcome to Vitalis AI! Dashboard synchronized.", "success");
    } catch (err) {
        console.error("Initialization error:", err);
        showToast("Error connecting to server. Please check backend status.", "error");
    }
    
    if (window.lucide) {
        lucide.createIcons();
    }
}

function setupDateDisplay() {
    const options = { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' };
    const today = new Date().toLocaleDateString('en-US', options);
    const dateEl = document.getElementById("currentDateDisplay");
    if (dateEl) dateEl.innerText = today;
}

// Navigation Tabs
function setupNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const tabId = item.getAttribute("data-tab");
            switchTab(tabId);
        });
    });

    const menuToggle = document.getElementById("menuToggle");
    if (menuToggle) {
        menuToggle.addEventListener("click", () => {
            document.getElementById("mainSidebar").classList.toggle("open");
        });
    }

    const openProfileBtn = document.getElementById("openProfileBtn");
    if (openProfileBtn) {
        openProfileBtn.addEventListener("click", () => {
            switchTab("profile");
        });
    }
}

function switchTab(tabId) {
    document.querySelectorAll(".nav-item").forEach(el => {
        el.classList.toggle("active", el.getAttribute("data-tab") === tabId);
    });

    document.querySelectorAll(".tab-content").forEach(el => {
        el.classList.toggle("active", el.id === `tab-${tabId}`);
    });

    if (window.innerWidth <= 768) {
        document.getElementById("mainSidebar").classList.remove("open");
    }

    if (tabId === "progress") {
        renderWeeklyChart();
    }
    
    if (window.lucide) {
        lucide.createIcons();
    }
}

// Profile
async function loadProfile() {
    try {
        const prof = await api.getProfile();
        state.profile = prof;
        
        // Update Nav
        document.getElementById("navUserName").innerText = prof.name;
        document.getElementById("avatarInitial").innerText = prof.name.charAt(0);
        
        // Fill Profile Form
        document.getElementById("profName").value = prof.name || "";
        document.getElementById("profAge").value = prof.age || 25;
        document.getElementById("profGender").value = prof.gender || "Other";
        document.getElementById("profHeight").value = prof.height_cm || 170;
        document.getElementById("profWeight").value = prof.weight_kg || 65;
        document.getElementById("profActivity").value = prof.activity_level || "Moderately Active";
        document.getElementById("profDiet").value = prof.dietary_pref || "Flexitarian";
        document.getElementById("profWakeTime").value = prof.wake_time || "06:30";
        document.getElementById("profSleepTime").value = prof.sleep_time || "22:30";
        document.getElementById("profWorkStart").value = prof.work_start || "09:00";
        document.getElementById("profWorkEnd").value = prof.work_end || "17:00";
        document.getElementById("profCooking").value = prof.cooking_facility || "Full Kitchen";
        
        // Update Targets UI
        document.getElementById("proteinTargetVal").innerText = `${prof.target_protein_g}g`;
        document.getElementById("fiberTargetVal").innerText = `${prof.target_fiber_g}g`;
        document.getElementById("waterTargetVal").innerText = `${(prof.target_water_ml / 1000).toFixed(2)} L`;
        document.getElementById("hydraPageTarget").innerText = (prof.target_water_ml / 1000).toFixed(2);
    } catch (e) {
        console.error("Failed to load profile", e);
    }
}

async function handleProfileSubmit(e) {
    e.preventDefault();
    const updatedData = {
        name: document.getElementById("profName").value,
        age: parseInt(document.getElementById("profAge").value),
        gender: document.getElementById("profGender").value,
        height_cm: parseFloat(document.getElementById("profHeight").value),
        weight_kg: parseFloat(document.getElementById("profWeight").value),
        activity_level: document.getElementById("profActivity").value,
        dietary_pref: document.getElementById("profDiet").value,
        allergies: state.profile?.allergies || [],
        disliked_foods: state.profile?.disliked_foods || [],
        favorite_foods: state.profile?.favorite_foods || [],
        wake_time: document.getElementById("profWakeTime").value,
        sleep_time: document.getElementById("profSleepTime").value,
        work_start: document.getElementById("profWorkStart").value,
        work_end: document.getElementById("profWorkEnd").value,
        cooking_facility: document.getElementById("profCooking").value,
        food_availability: state.profile?.food_availability || "Standard Groceries",
        preferred_meal_times: state.profile?.preferred_meal_times || {}
    };

    try {
        const res = await api.updateProfile(updatedData);
        state.profile = res;
        showToast("Profile updated & targets recalculated successfully!", "success");
        await loadProgress();
        switchTab("dashboard");
    } catch (err) {
        showToast("Failed to save profile: " + err.message, "error");
    }
}

// Meal Plan
async function loadMealPlan() {
    try {
        const plan = await api.getTodayMealPlan();
        state.mealPlan = plan;
        renderMealCards(plan.meals);
        renderMacroChart(plan.meals);
    } catch (err) {
        console.error("Failed to load meal plan:", err);
    }
}

function renderMealCards(meals) {
    const container = document.getElementById("mealsListContainer");
    const fullContainer = document.getElementById("mealsFullListContainer");
    
    if (!meals || meals.length === 0) {
        container.innerHTML = `<div class="empty-state">No meals scheduled for today.</div>`;
        if (fullContainer) fullContainer.innerHTML = container.innerHTML;
        return;
    }

    const html = meals.map(m => {
        const isDone = m.status === "completed";
        const isSkipped = m.status === "skipped";
        const statusClass = isDone ? "completed" : (isSkipped ? "skipped" : "");

        const itemsHtml = m.items.map(it => `
            <span class="item-chip">
                ${it.food_name}: <span class="raw-qty">${it.raw_quantity}${it.unit}</span>
                ${it.cooked_quantity && it.cooked_quantity !== it.raw_quantity ? `<small>(${it.cooked_quantity}g cooked)</small>` : ''}
                <button class="btn-sub-trigger" title="Substitute ingredient" onclick="openSubstitutionModal('${m.id}', '${it.food_id}', '${it.food_name}', ${it.raw_quantity})">⇄</button>
            </span>
        `).join("");

        return `
            <div class="meal-card ${statusClass}" id="meal-card-${m.id}">
                <div class="meal-header-row">
                    <span class="meal-type-badge">${m.meal_type.replace('_', ' ')}</span>
                    <span class="meal-time-tag"><i data-lucide="clock" style="width: 14px; height:14px;"></i> ${m.scheduled_time}</span>
                </div>
                <h4 class="meal-name">${m.name}</h4>
                <div class="meal-items-tags">
                    ${itemsHtml}
                </div>
                <div class="meal-macro-badges">
                    <div class="m-badge"><strong>${m.calories}</strong> kcal</div>
                    <div class="m-badge" style="color: var(--primary-light);">Protein: <strong>${m.protein}g</strong></div>
                    <div class="m-badge" style="color: #a78bfa;">Fiber: <strong>${m.fiber}g</strong></div>
                    <div class="m-badge" style="color: #38bdf8;">Carbs: <strong>${m.carbs}g</strong></div>
                    <div class="m-badge" style="color: #fbbf24;">Fat: <strong>${m.fat}g</strong></div>
                </div>
                <div class="meal-actions-row">
                    <div class="prep-notes-hint" title="${m.prep_notes || ''}">
                        💡 ${m.prep_notes || 'Standard balanced preparation'}
                    </div>
                    <div class="action-btns-group">
                        <button class="btn btn-sm ${isDone ? 'btn-success' : 'btn-outline-primary'}" onclick="toggleMealCompletion('${m.id}')">
                            <i data-lucide="${isDone ? 'check-circle' : 'circle'}"></i>
                            <span>${isDone ? 'Completed' : 'Complete'}</span>
                        </button>
                        ${!isDone && !isSkipped ? `
                            <button class="btn btn-sm btn-outline-secondary" onclick="markMealSkipped('${m.id}')">
                                <span>Skip</span>
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join("");

    container.innerHTML = html;
    if (fullContainer) fullContainer.innerHTML = html;
    
    if (window.lucide) {
        lucide.createIcons();
    }
}

async function toggleMealCompletion(mealId) {
    try {
        await api.completeMeal(mealId);
        await Promise.all([loadMealPlan(), loadProgress()]);
        showToast("Meal status updated!", "success");
    } catch (err) {
        showToast("Failed to update meal: " + err.message, "error");
    }
}

async function markMealSkipped(mealId) {
    try {
        await api.skipMeal(mealId);
        await Promise.all([loadMealPlan(), loadProgress()]);
        showToast("Meal marked as skipped. Adaptive Agent notified.", "info");
    } catch (err) {
        showToast("Failed to skip meal: " + err.message, "error");
    }
}

// Hydration
async function loadHydration() {
    try {
        const hydra = await api.getTodayHydration();
        state.hydration = hydra;
        
        const liters = (hydra.consumed_ml / 1000).toFixed(2);
        const targetLiters = (hydra.target_ml / 1000).toFixed(2);
        const remainingLiters = (hydra.remaining_ml / 1000).toFixed(2);
        
        // KPI Card
        document.getElementById("waterConsumedVal").innerText = liters;
        document.getElementById("waterProgressBar").style.width = `${Math.min(100, hydra.percentage)}%`;
        
        // Hydration Page
        document.getElementById("hydraPageConsumed").innerText = liters;
        document.getElementById("hydraPageRemaining").innerText = `${remainingLiters} L remaining to reach daily hydration estimate`;
        
        // History List
        const histContainer = document.getElementById("waterHistoryList");
        if (hydra.logs.length === 0) {
            histContainer.innerHTML = `<div class="empty-state">No water logged yet today. Click +250ml to start!</div>`;
        } else {
            histContainer.innerHTML = hydra.logs.map(log => `
                <div class="water-log-item">
                    <div>
                        <strong>+${log.amount_ml} ml</strong>
                        <span style="font-size:0.75rem; color:var(--text-muted); margin-left: 8px;">${log.timestamp.split('T')[1]?.substring(0, 5) || 'Just now'}</span>
                    </div>
                    <button class="btn btn-sm btn-outline-secondary" onclick="deleteWater('${log.id}')">&times;</button>
                </div>
            `).join("");
        }
    } catch (e) {
        console.error("Hydration load error", e);
    }
}

async function logQuickWater(amount) {
    try {
        await api.logWater(amount, "quick_button");
        await Promise.all([loadHydration(), loadProgress()]);
        showToast(`Logged +${amount} ml water!`, "success");
    } catch (err) {
        showToast("Error logging water: " + err.message, "error");
    }
}

async function handleCustomWaterSubmit(e) {
    e.preventDefault();
    const amount = parseFloat(document.getElementById("customWaterInput").value);
    if (!amount || amount <= 0) return;
    
    try {
        await api.logWater(amount, "custom_input");
        document.getElementById("customWaterInput").value = "";
        await Promise.all([loadHydration(), loadProgress()]);
        showToast(`Logged +${amount} ml water!`, "success");
    } catch (err) {
        showToast("Error logging custom water: " + err.message, "error");
    }
}

async function deleteWater(logId) {
    try {
        await api.deleteWaterLog(logId);
        await Promise.all([loadHydration(), loadProgress()]);
        showToast("Water entry removed.", "info");
    } catch (err) {
        showToast("Failed to delete entry: " + err.message, "error");
    }
}

// Progress & Totals
async function loadProgress() {
    try {
        const prog = await api.getTodayProgress();
        state.progress = prog;
        const s = prog.summary;
        
        // Protein
        document.getElementById("proteinConsumedVal").innerText = s.protein.consumed_g;
        document.getElementById("proteinRemainingLabel").innerText = `${s.protein.remaining_g}g remaining`;
        document.getElementById("proteinPlannedHint").innerText = `Planned: ${s.protein.planned_g}g`;
        const protPct = Math.min(100, Math.round((s.protein.consumed_g / Math.max(1, s.protein.target_g)) * 100));
        document.getElementById("proteinProgressBar").style.width = `${protPct}%`;
        
        // Fiber
        document.getElementById("fiberConsumedVal").innerText = s.fiber.consumed_g;
        document.getElementById("fiberRemainingLabel").innerText = `${s.fiber.remaining_g}g remaining`;
        document.getElementById("fiberPlannedHint").innerText = `Planned: ${s.fiber.planned_g}g`;
        const fiberPct = Math.min(100, Math.round((s.fiber.consumed_g / Math.max(1, s.fiber.target_g)) * 100));
        document.getElementById("fiberProgressBar").style.width = `${fiberPct}%`;
        
        // Adherence
        document.getElementById("adherenceScoreVal").innerText = s.adherence_score;
        document.getElementById("mealsCompletedTag").innerText = `${s.meals_completed} / ${s.meals_total} Meals`;
        document.getElementById("adherenceProgressBar").style.width = `${s.adherence_score}%`;
        document.getElementById("caloriesSummaryLabel").innerText = `${s.calories.consumed} / ${s.calories.target} kcal consumed`;
    } catch (e) {
        console.error("Progress load error", e);
    }
}

// Macro Chart
function renderMacroChart(meals) {
    const ctx = document.getElementById("macroDistributionChart");
    if (!ctx) return;
    
    const labels = meals.map(m => m.meal_type.replace('_', ' ').toUpperCase());
    const proteinData = meals.map(m => m.protein);
    const fiberData = meals.map(m => m.fiber);
    
    if (state.charts.macroChart) {
        state.charts.macroChart.destroy();
    }
    
    state.charts.macroChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Protein (g)',
                    data: proteinData,
                    backgroundColor: '#10b981',
                    borderRadius: 6
                },
                {
                    label: 'Fiber (g)',
                    data: fiberData,
                    backgroundColor: '#8b5cf6',
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans' } }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#94a3b8', font: { size: 11 } },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                y: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                }
            }
        }
    });
}

// Weekly Chart
async function renderWeeklyChart() {
    const ctx = document.getElementById("weeklyTrendsChart");
    if (!ctx) return;
    
    try {
        const weekly = await api.getWeeklyProgress();
        const labels = weekly.days.map(d => d.day_name);
        const adherenceData = weekly.days.map(d => d.adherence);
        const proteinData = weekly.days.map(d => d.protein_g);
        
        if (state.charts.weeklyChart) {
            state.charts.weeklyChart.destroy();
        }
        
        state.charts.weeklyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Meal Adherence (%)',
                        data: adherenceData,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.15)',
                        fill: true,
                        tension: 0.35
                    },
                    {
                        label: 'Protein Logged (g)',
                        data: proteinData,
                        borderColor: '#38bdf8',
                        backgroundColor: 'transparent',
                        borderDash: [5, 5],
                        tension: 0.35
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#94a3b8' } }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } }
                }
            }
        });
    } catch (e) {
        console.error("Weekly chart error", e);
    }
}

// Food Database Explorer
async function loadFoods() {
    try {
        const foods = await api.searchFoods();
        state.allFoods = foods;
        renderFoodTable(foods);
        populateSubstitutionSelect(foods);
    } catch (e) {
        console.error("Foods loading error", e);
    }
}

function renderFoodTable(foods) {
    const tbody = document.getElementById("foodTableBody");
    if (!tbody) return;
    
    tbody.innerHTML = foods.map(f => `
        <tr>
            <td><strong>${f.name}</strong></td>
            <td><span class="meal-type-badge">${f.category}</span></td>
            <td>${f.serving_desc || '100g'}</td>
            <td>${f.calories_per_100g}</td>
            <td style="color:var(--primary-light);"><strong>${f.protein_per_100g}g</strong></td>
            <td>${f.carbohydrates_per_100g}g</td>
            <td>${f.fat_per_100g}g</td>
            <td style="color:#a78bfa;"><strong>${f.fiber_per_100g}g</strong></td>
            <td>
                <button class="btn btn-sm btn-glass" onclick="testPortionCalc('${f.food_id}')">Calc 100g</button>
            </td>
        </tr>
    `).join("");
}

let searchTimer = null;
function debounceFoodSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(async () => {
        const query = document.getElementById("foodSearchInput").value;
        const foods = await api.searchFoods(query);
        renderFoodTable(foods);
    }, 250);
}

// Substitution Modal
function populateSubstitutionSelect(foods) {
    const select = document.getElementById("subFoodSelect");
    if (!select) return;
    select.innerHTML = foods.map(f => `
        <option value="${f.food_id}">${f.name} (${f.category}) - ${f.protein_per_100g}g P / 100g</option>
    `).join("");
}

function openSubstitutionModal(mealId, foodId, foodName, currentQty) {
    document.getElementById("subMealId").value = mealId;
    document.getElementById("subOriginalFoodId").value = foodId;
    document.getElementById("substitutePromptText").innerText = `Replacing "${foodName}" in this meal with a nutrient-equivalent food:`;
    document.getElementById("subQuantityInput").value = currentQty;
    
    document.getElementById("substitutionModal").classList.add("active");
    updateSubstitutionPreview();
}

function closeSubstitutionModal() {
    document.getElementById("substitutionModal").classList.remove("active");
}

async function updateSubstitutionPreview() {
    const foodId = document.getElementById("subFoodSelect").value;
    const qty = parseFloat(document.getElementById("subQuantityInput").value) || 0;
    if (!foodId || qty <= 0) return;
    
    try {
        const calc = await api.calculatePortion(foodId, qty);
        const n = calc.nutrition;
        document.getElementById("subPrevCals").innerText = `${n.calories} kcal`;
        document.getElementById("subPrevProt").innerText = `${n.protein} g`;
        document.getElementById("subPrevCarbs").innerText = `${n.carbohydrates} g`;
        document.getElementById("subPrevFiber").innerText = `${n.fiber} g`;
    } catch (e) {
        console.error("Preview calc error", e);
    }
}

async function confirmSubstitution() {
    const mealId = document.getElementById("subMealId").value;
    const originalFoodId = document.getElementById("subOriginalFoodId").value;
    const subFoodId = document.getElementById("subFoodSelect").value;
    const qty = parseFloat(document.getElementById("subQuantityInput").value);
    
    try {
        const res = await api.substituteMealItem(mealId, originalFoodId, subFoodId, qty, "User selected substitute");
        showToast(res.message || "Food substituted successfully!", "success");
        closeSubstitutionModal();
        await Promise.all([loadMealPlan(), loadProgress()]);
    } catch (err) {
        showToast("Substitution failed: " + err.message, "error");
    }
}

async function testPortionCalc(foodId) {
    const calc = await api.calculatePortion(foodId, 100);
    showToast(`100g ${calc.food_name}: ${calc.nutrition.calories} kcal, ${calc.nutrition.protein}g protein, ${calc.nutrition.fiber}g fiber`, "info");
}

// Toast System
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;
    
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerText = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Global functions for inline HTML event handlers
window.logQuickWater = logQuickWater;
window.handleCustomWaterSubmit = handleCustomWaterSubmit;
window.deleteWater = deleteWater;
window.loadMealPlan = loadMealPlan;
window.toggleMealCompletion = toggleMealCompletion;
window.markMealSkipped = markMealSkipped;
window.handleProfileSubmit = handleProfileSubmit;
window.openSubstitutionModal = openSubstitutionModal;
window.closeSubstitutionModal = closeSubstitutionModal;
window.updateSubstitutionPreview = updateSubstitutionPreview;
window.confirmSubstitution = confirmSubstitution;
window.testPortionCalc = testPortionCalc;
window.debounceFoodSearch = debounceFoodSearch;
window.switchTab = switchTab;
