/*
 * Copyright (C) 2026 johannesjh
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
}

// ---- Login page ----
(function () {
    const form = document.getElementById("login-form");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const btn = form.querySelector('button[type="submit"]');
        const errEl = document.getElementById("login-error");
        btn.disabled = true;
        btn.textContent = "Bitte warten...";
        errEl.style.display = "none";

        const data = {
            username: document.getElementById("username").value,
            password: document.getElementById("password").value,
        };

        try {
            const resp = await fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
                credentials: "same-origin",
            });
            const json = await resp.json();
            if (resp.ok && json.ok) {
                window.location.href = "/dashboard";
            } else {
                errEl.textContent = json.error || "Anmeldung fehlgeschlagen";
                errEl.style.display = "block";
            }
        } catch (err) {
            errEl.textContent = "Verbindungsfehler";
            errEl.style.display = "block";
        } finally {
            btn.disabled = false;
            btn.textContent = "Anmelden";
        }
    });
})();

// ---- Logout button ----
(function () {
    const btn = document.getElementById("logout-btn");
    if (!btn) return;
    btn.addEventListener("click", async () => {
        try {
            await fetch("/api/logout", {
                method: "POST",
                headers: { "X-CSRF-Token": getCsrfToken() },
                credentials: "same-origin",
            });
        } finally {
            window.location.href = "/login";
        }
    });
})();

// ---- Dashboard / View page: cards, refresh, actions ----
(function () {
    // Only activate on pages that have cards
    if (!document.querySelector(".card")) return;

    const refreshBtn = document.getElementById("refresh-btn");

    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            refreshBtn.querySelector(".refresh-icon").classList.add("spinning");
            loadAllCards();
        });
    }

    // Pull-to-refresh support
    let startY = 0;
    document.addEventListener("touchstart", (e) => {
        startY = e.touches[0].clientY;
    }, { passive: true });

    document.addEventListener("touchend", (e) => {
        const endY = e.changedTouches[0].clientY;
        if (endY - startY > 100 && window.scrollY === 0 && refreshBtn) {
            refreshBtn.querySelector(".refresh-icon").classList.add("spinning");
            loadAllCards();
        }
    }, { passive: true });

    // Action buttons
    document.querySelectorAll(".btn-action").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const cardName = btn.dataset.card;
            const origText = btn.textContent;
            btn.textContent = "Wird ausgeführt...";
            btn.disabled = true;

            try {
                const resp = await fetch("/api/actions/" + cardName, {
                    method: "POST",
                    headers: { "X-CSRF-Token": getCsrfToken() },
                    credentials: "same-origin",
                });
                const json = await resp.json();
                if (resp.ok && json.ok) {
                    showToast("Aktion erfolgreich", "success");
                    loadAllCards();
                } else {
                    showToast(json.error || "Aktion fehlgeschlagen", "error");
                }
            } catch (err) {
                showToast("Verbindungsfehler", "error");
            } finally {
                btn.textContent = origText;
                btn.disabled = false;
            }
        });
    });

    // Toggle buttons
    document.querySelectorAll(".btn-toggle").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const cardName = btn.dataset.card;
            const cardEl = btn.closest(".card");
            const valEl = cardEl ? cardEl.querySelector(".toggle-value") : null;

            // Determine current state from DOM before toggling
            const currentlyOn = valEl ? valEl.classList.contains("status-on") : null;

            btn.disabled = true;
            btn.querySelector(".toggle-label").textContent = "Wird umgeschaltet...";

            try {
                const resp = await fetch("/api/actions/" + cardName, {
                    method: "POST",
                    headers: { "X-CSRF-Token": getCsrfToken() },
                    credentials: "same-origin",
                });
                const json = await resp.json();
                if (resp.ok && json.ok) {
                    // Optimistic UI update: flip the state locally without re-fetching from HA.
                    // Re-fetching immediately after toggle would return the stale state for
                    // real devices (e.g. Shelly plugs) that have a short switching delay.
                    if (currentlyOn !== null) {
                        const newIsOn = !currentlyOn;
                        if (valEl) {
                            valEl.textContent = newIsOn ? "An" : "Aus";
                            valEl.classList.remove("status-on", "status-off");
                            valEl.classList.add(newIsOn ? "status-on" : "status-off");
                        }
                        btn.querySelector(".toggle-label").textContent = newIsOn ? "Ausschalten" : "Anschalten";
                    }
                    showToast("Umgeschaltet", "success");
                } else {
                    showToast(json.error || "Umschalten fehlgeschlagen", "error");
                    // Restore label on failure
                    if (currentlyOn !== null) {
                        btn.querySelector(".toggle-label").textContent = currentlyOn ? "Ausschalten" : "Anschalten";
                    }
                }
            } catch (err) {
                showToast("Verbindungsfehler", "error");
                if (currentlyOn !== null) {
                    btn.querySelector(".toggle-label").textContent = currentlyOn ? "Ausschalten" : "Anschalten";
                }
            } finally {
                btn.disabled = false;
            }
        });
    });

    // Initial load
    loadAllCards();
})();

async function loadAllCards() {
    const cards = document.querySelectorAll(".card");
    const promises = [];

    cards.forEach((card) => {
        const cardName = card.dataset.cardName;
        const cardType = card.dataset.cardType;
        promises.push(loadCardData(cardName, cardType, card));
    });

    await Promise.all(promises);

    // Remove spinning animation
    const icon = document.querySelector(".refresh-icon");
    if (icon) icon.classList.remove("spinning");
}

async function loadCardData(cardName, cardType, cardEl) {
    const statusEl = cardEl.querySelector(".card-status");

    // Action- und Staticinfo-Cards haben keinen Datenabruf
    if (cardType === "action" || cardType === "staticinfo") return;

    try {
        const resp = await fetch("/api/card/" + cardName + "/data", {
            method: "GET",
            credentials: "same-origin",
        });
        const json = await resp.json();

        if (!json.available) {
            setStatus(statusEl, false);
            return;
        }

        setStatus(statusEl, true);

        if (cardType === "status") {
            const valEl = cardEl.querySelector(".status-value");
            if (valEl) valEl.textContent = formatValue(json.value, json.attributes);
        } else if (cardType === "sensor") {
            const valEl = cardEl.querySelector(".sensor-value");
            const attrEl = cardEl.querySelector(".sensor-attributes");
            if (valEl) valEl.textContent = formatValue(json.value, json.attributes);
            if (attrEl && json.attributes) {
                const units = json.attributes.unit_of_measurement;
                if (units) attrEl.textContent = units;
            }
        } else if (cardType === "toggle") {
            const valEl = cardEl.querySelector(".toggle-value");
            const btn = cardEl.querySelector(".btn-toggle");
            const isOn = json.value && json.value.toLowerCase() === "on";

            if (valEl) {
                valEl.textContent = isOn ? "An" : "Aus";
                valEl.classList.remove("status-on", "status-off");
                valEl.classList.add(isOn ? "status-on" : "status-off");
            }
            if (btn) {
                btn.classList.remove("toggled-on");
                btn.querySelector(".toggle-label").textContent = isOn ? "Ausschalten" : "Anschalten";
            }
        }
    } catch (err) {
        setStatus(statusEl, false);
    }
}

function setStatus(el, available) {
    if (!el) return;
    el.classList.toggle("available", available);
    el.classList.toggle("unavailable", !available);
    el.textContent = available ? "Verfügbar" : "Nicht verfügbar";
}

function formatValue(value, attributes) {
    if (value === null || value === undefined) return "--";
    const str = String(value);
    if (attributes && attributes.unit_of_measurement) {
        return str + " " + attributes.unit_of_measurement;
    }
    return str;
}

function showToast(message, type) {
    const toast = document.getElementById("toast");
    if (!toast) return;

    // Icon hinzufügen
    const icon = type === 'success' 
        ? '<svg class="toast-icon" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg>'
        : '<svg class="toast-icon" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>';

    toast.innerHTML = icon + '<span>' + message + '</span>';
    
    // WICHTIG: Display auf flex setzen, damit es überhaupt Platz einnimmt
    toast.style.display = "flex"; 
    
    // Klassen setzen
    toast.className = "toast " + type; 
    
    requestAnimationFrame(() => {
        toast.classList.add("show");
    });
    
    setTimeout(function () {
        toast.classList.remove("show");
        // Nach der Animation wieder auf none setzen
        setTimeout(() => {
            toast.style.display = "none";
        }, 300);
    }, 3000);
}
